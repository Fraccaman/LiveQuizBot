import operator
import re
import string
from urllib.parse import quote
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from multiprocessing.pool import ThreadPool
from typing import List, Dict

import nltk
import requests
from bs4 import BeautifulSoup, SoupStrainer
from num2words import num2words
from unidecode import unidecode

from src.costants import IT_STOP_WORDS, DOMAIN, HEADERS, Colors, COMMA_REMOVE
from src.instance import Instance, SolverType
from src.parallel_process import parallel_execution
from src.utlity import timeit


@dataclass
class Solver(ABC):
    pool: ThreadPool
    type: SolverType
    original: Instance = field(init=False)
    copy: Instance = field(init=False)
    fields: List = field(default_factory=lambda: ['question', 'first_answer', 'second_answer', 'third_answer'])
    ita_stemmer = nltk.stem.snowball.ItalianStemmer()
    req = requests.Session()

    @abstractmethod
    def is_valid_type(self, instance: Instance):
        raise Exception("Not implemented")

    def clean_impl(self, f: str):
        to_clean = self.copy.__dict__[f]
        if len(to_clean.split(' ')) == 1:
            to_clean = to_clean.lower()
            to_clean = to_clean.translate(str.maketrans('', '', string.punctuation))
            self.copy.__dict__[f] = unidecode(to_clean).strip()
        elif (f == 'first_answer' and self.copy.is_first_complete_ner) or (
                f == 'second_answer' and self.copy.is_second_complete_ner) or (
                f == 'third_answer' and self.copy.is_third_complete_ner):
            to_clean = to_clean.lower()
            to_clean = to_clean.translate(str.maketrans('', '', string.punctuation))
            self.copy.__dict__[f] = unidecode(to_clean).strip()
        else:
            to_clean = to_clean.lower()
            is_mandatory = re.search('"(.*)"', to_clean).group(1) if to_clean.count('\"') == 2 else ''
            word_tokenized_list = nltk.tokenize.word_tokenize(to_clean)
            word_tokenized_no_punct = [x.lower() for x in word_tokenized_list if x not in string.punctuation]
            word_tokenized_no_punct_no_sw = [x for x in word_tokenized_no_punct if
                                             x not in set(IT_STOP_WORDS)]
            word_tokenized_no_punct_no_sw_no_apostrophe = [x.split("'") for x in word_tokenized_no_punct_no_sw]
            word_tokenized_no_punct_no_sw_no_apostrophe = [y for x in word_tokenized_no_punct_no_sw_no_apostrophe for y in
                                                           x]

            if f != 'question':
                self.copy.__dict__[f] = ' '.join(unidecode(' '.join(word_tokenized_no_punct_no_sw_no_apostrophe)).split())
            else:
                if is_mandatory != '':
                    q = ' '.join(word_tokenized_no_punct_no_sw_no_apostrophe).replace(is_mandatory, '"{}"'.format(is_mandatory))
                    self.copy.__dict__[f] = unidecode(q).strip()
                else:
                    self.copy.__dict__[f] = unidecode(' '.join(word_tokenized_no_punct_no_sw_no_apostrophe)).strip()

        if f == self.fields[1]:
            self.copy.indexes[self.copy.__dict__[f]] = 0
        elif f == self.fields[2]:
            self.copy.indexes[self.copy.__dict__[f]] = 1
        elif f == self.fields[3]:
            self.copy.indexes[self.copy.__dict__[f]] = 2

    def clean(self):
        question = self.copy.to_lower('question').split(', ')
        self.copy.question = ''
        for q in question:
            if any(word in q for word in COMMA_REMOVE) and q[0] in COMMA_REMOVE:
                self.copy.question += q
        if not self.copy.question or self.original.to_lower('question').count('\"') > 1: self.copy.question = self.original.to_lower('question')
        parallel_execution(self.pool, self.clean_impl, self.fields)

    def _init(self, instance: Instance):
        self.original = instance
        self.copy = deepcopy(instance)

    def craft_queries(self):
        return [
            DOMAIN + self.copy.question,
            DOMAIN + quote('{} AND {}'.format(self.copy.question, self.copy.first_answer)),
            DOMAIN + quote('{} AND {}'.format(self.copy.question, self.copy.second_answer)),
            DOMAIN + quote('{} AND {}'.format(self.copy.question, self.copy.third_answer))
        ]

    @timeit
    def get_page(self, url: str):
        return self.req.get(url, headers=HEADERS).text

    @staticmethod
    def find_occurences(to_search: str, to_find: str):
        return re.finditer(r'\b%s\b' % re.escape(to_find), to_search)

    @timeit
    def get_points_from_texts(self, html: str):
        strainer = SoupStrainer('div', {'class': 'srg', })
        soup = BeautifulSoup(html, 'lxml', parse_only=strainer)
        all_links = soup.find_all('div', {'class': 'g', })

        points = {
            self.copy.to_lower('first_answer'): 0,
            self.copy.to_lower('second_answer'): 0,
            self.copy.to_lower('third_answer'): 0
        }

        # TODO: better parallelize
        args = [[link, deepcopy(points)] for link in all_links]
        res = ThreadPool(6).map(self.get_points_link, args)
        res = ({k: sum([x[k] for x in res if k in x]) for i in res for k, v in i.items()})

        return res

    @staticmethod
    def remove_accent_punctuation(s):
        s = unidecode(s)
        s.translate(str.maketrans('', '', string.punctuation))
        return s

    def get_points_link(self, data: List):
        try:
            title = self.remove_accent_punctuation(data[0].find('div', {'class': 'r'}).find('h3').text.lower())
            description = self.remove_accent_punctuation(data[0].find('div', {'class': 's'}).find('span', {'class': 'st'}).text.lower())
        except Exception as e:
            return data[1]

        for index, answer in enumerate(data[1].keys()):
            count_title = 0
            count_description = 0

            if (index == 0 and self.copy.is_first_complete_ner) or (
                    index == 1 and self.copy.is_second_complete_ner) or (
                    index == 2 and self.copy.is_third_complete_ner):
                count_title += sum(1 for _ in self.find_occurences(title, answer))
                if count_title == 0: count_title += 1 if ' ' + answer + ' ' in title else 0
                count_description += sum(1 for _ in self.find_occurences(description, answer))
                if count_description == 0: count_description += 1 if ' ' + answer + '' in description else 0

                data[1][answer] += count_title + count_description
            else:
                for word in answer.split(' '):
                    if word.strip() and (len(word) > 1 or word.isdigit()):
                        count_title += sum(1 for _ in self.find_occurences(title, word))
                        count_description += sum(1 for _ in self.find_occurences(description, word))
                        if word.isdigit():
                            int_to_word = num2words(int(word), lang='it')
                            count_title += sum(1 for _ in self.find_occurences(title, int_to_word))
                            count_description += sum(1 for _ in self.find_occurences(description, int_to_word))

                data[1][answer] += count_title + count_description
        return data[1]

    def select_points(self, points: List[Dict[str, int]]):
        return points[0]

    @staticmethod
    def _print_score(n, res, index, win=False):
        print('{}{}: {}{} - score: {}'.format(Colors.BOLD if not win else Colors.BOLD + Colors.RED, n, res[index][0].upper(), Colors.END, res[index][1]))

    def print_results(self, point: Dict[str, int]):
        scores = sorted(point.values())

        tmp_res = list(point.items())

        # hacky but needed if score of first two equal but one of the two has more words
        if tmp_res[0][1] == tmp_res[1][1] and len(tmp_res[0][0].split(' ')) > 1 and len(tmp_res[1][0].split(' ')) > 1:
            if len(tmp_res[0][0]) < len(tmp_res[1][0]):
                point[tmp_res[1][0]] = 0
            else:
                point[tmp_res[0][0]] = 0

        res = [None, None, None]
        tmp_res = list(point.items())

        for i in range(len(tmp_res)):
            org_answer_index = self.copy.indexes[tmp_res[i][0]]
            if org_answer_index == 0:
                res[0] = (self.original.first_answer, tmp_res[i][1])
            elif org_answer_index == 1:
                res[1] = (self.original.second_answer, tmp_res[i][1])
            else:
                res[2] = (self.original.third_answer, tmp_res[i][1])

        if self.copy.is_negative:
            res = list(sorted(res, key=operator.itemgetter(1)))
        else:
            res = list(reversed(sorted(res, key=operator.itemgetter(1))))

        if all(score == 0 for score in scores):
            self._print_score(1, res, 0)
            self._print_score(2, res, 1)
            self._print_score(3, res, 2)
        else:
            self._print_score(1, res, 0, win=True)
            self._print_score(2, res, 1)
            self._print_score(3, res, 2)

        return dict(res)

    def count_points(self, queries: List[str]):
        res = parallel_execution(self.pool, self.get_page, queries)

        points = parallel_execution(self.pool, self.get_points_from_texts, res)
        point = self.select_points(points)
        return self.print_results(point)

    def clean_for_points(self):
        s1 = set([self.ita_stemmer.stem(i) for i in self.copy.first_answer.split(' ')])
        s2 = set([self.ita_stemmer.stem(i) for i in self.copy.second_answer.split(' ')])
        s3 = set([self.ita_stemmer.stem(i) for i in self.copy.third_answer.split(' ')])
        test = s1.intersection(s2, s3)
        if not len(test) == 0:
            s1_new = [word for word in self.copy.first_answer.split(' ') if not self.ita_stemmer.stem(word) in test]
            s2_new = [word for word in self.copy.second_answer.split(' ') if not self.ita_stemmer.stem(word) in test]
            s3_new = [word for word in self.copy.third_answer.split(' ') if not self.ita_stemmer.stem(word) in test]
            self.copy.first_answer = ' '.join(s1_new)
            self.copy.second_answer = ' '.join(s2_new)
            self.copy.third_answer = ' '.join(s3_new)

            self.copy.indexes[self.copy.first_answer] = 0
            self.copy.indexes[self.copy.second_answer] = 1
            self.copy.indexes[self.copy.third_answer] = 2

    def solve(self, instance: Instance):
        self._init(instance)
        self.clean()
        queries = self.craft_queries()
        self.clean_for_points()
        return self.count_points(queries)
