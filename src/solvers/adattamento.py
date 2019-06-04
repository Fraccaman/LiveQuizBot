import string
from dataclasses import dataclass

import nltk
from unidecode import unidecode

from src.costants import IT_STOP_WORDS
from src.parallel_process import parallel_execution
from src.solvers.solver import Solver
from src.utlity import timeit


@dataclass
class Adattamento(Solver):

    def is_valid_type(self, instance):
        return self.type == instance.solver

    def craft_queries(self):
        return [
            self.original.first_answer,
            self.original.second_answer,
            self.original.third_answer
        ]

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
        return ' '.join(self.clean_summary(self.wiki.page(urls[0]).summary))

    def count(self, summaries):

        print(summaries)

        points = {
            self.copy.first_answer: 0,
            self.copy.second_answer: 0,
            self.copy.third_answer: 0
        }

        for index, summary in enumerate(summaries):
            if index == 0:
                points[self.copy.first_answer] = summary.count(' film ')
            elif index == 1:
                points[self.copy.second_answer] = summary.count(' film ')
            elif index == 2:
                points[self.copy.third_answer] = summary.count(' film ')

        return points

    @timeit
    def count_points(self, queries):
        res = parallel_execution(self.pool, self.wiki.search, queries)
        summaries = parallel_execution(self.pool, self.get_page, res)
        point = self.count(summaries)
        return self.print_results(point)
