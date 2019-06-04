import string
from dataclasses import dataclass
from typing import List, Dict
from urllib.parse import quote

import nltk
from bs4 import BeautifulSoup
from unidecode import unidecode
from wikipedia import wikipedia

from src.costants import DOMAIN, Colors, IT_STOP_WORDS
from src.parallel_process import parallel_execution
from src.solvers.solver import Solver
from src.utlity import timeit


@dataclass
class Intruso(Solver):

    def is_valid_type(self, instance):
        return self.type == instance.solver

    def craft_queries(self):
        return [
            self.original.first_answer,
            self.original.second_answer,
            self.original.third_answer
        ]

    def get_result_number(self, html):
        soup = BeautifulSoup(html, 'lxml')
        try:
            results_text = soup.find('div', {'id': 'resultStats'}).text
        except Exception as _:
            return 0
        num = results_text.split(' ')[1].replace('’', '').replace(',', '')
        return int(num) if num.isdigit() else 0

    def clean_summary(self, text):
        to_clean = unidecode(text.lower())
        word_tokenized_list = nltk.tokenize.word_tokenize(to_clean)
        word_tokenized_no_punct = [x.lower() for x in word_tokenized_list if x not in string.punctuation]
        word_tokenized_no_punct_no_sw = [x for x in word_tokenized_no_punct if
                                         x not in set(IT_STOP_WORDS)]
        word_tokenized_no_punct_no_sw_no_apostrophe = [x.split("'") for x in word_tokenized_no_punct_no_sw]
        word_tokenized_no_punct_no_sw_no_apostrophe = [y for x in word_tokenized_no_punct_no_sw_no_apostrophe for y
                                                       in x]
        last = [x for x in word_tokenized_no_punct_no_sw_no_apostrophe if
                x not in set(IT_STOP_WORDS)]

        return last

    def get_page(self, urls):
        return set(self.clean_summary(self.wiki.page(urls[0]).summary))

    def count(self, summaries):
        one_two_ratio = len(summaries[0].intersection(summaries[1])) / len(
            summaries[0].symmetric_difference(summaries[1]))
        one_three_ratio = len(summaries[0].intersection(summaries[2])) / len(
            summaries[0].symmetric_difference(summaries[2]))
        two_three_ratio = len(summaries[1].intersection(summaries[2])) / len(
            summaries[1].symmetric_difference(summaries[2]))

        if one_two_ratio > one_three_ratio and one_two_ratio > two_three_ratio:
            return {
                self.copy.first_answer: 0,
                self.copy.second_answer: 0,
                self.copy.third_answer: 1
            }
        elif one_three_ratio > one_two_ratio and one_three_ratio > two_three_ratio:
            return {
                self.copy.first_answer: 0,
                self.copy.second_answer: 1,
                self.copy.third_answer: 0
            }
        elif two_three_ratio > one_three_ratio and two_three_ratio > one_two_ratio:
            return {
                self.copy.first_answer: 1,
                self.copy.second_answer: 0,
                self.copy.third_answer: 0
            }

    @timeit
    def count_points(self, queries):
        res = parallel_execution(self.pool, self.wiki.search, queries)
        summaries = parallel_execution(self.pool, self.get_page, res)
        point = self.count(summaries)
        return self.print_results(point)
