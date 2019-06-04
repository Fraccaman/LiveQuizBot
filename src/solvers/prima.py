import itertools
import re
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Dict
from urllib.parse import quote

import italian_dictionary
from bs4 import BeautifulSoup
from dateutil.parser import parse

from src.costants import DOMAIN
from src.instance import Instance
from src.solvers.solver import Solver


@dataclass
class Prima(Solver):

    def is_valid_type(self, instance: Instance):
        return self.type == instance.solver

    def craft_queries(self):
        not_found = 0
        try:
            _ = italian_dictionary.get_only_definition(self.original.first_answer, limit=1)
        except Exception as _:
            not_found = not_found + 1

        try:
            _ = italian_dictionary.get_only_definition(self.original.second_answer, limit=1)
        except Exception as _:
            not_found = not_found + 1

        try:
            _ = italian_dictionary.get_only_definition(self.original.third_answer, limit=1)
        except Exception as _:
            not_found = not_found + 1

        # self.clean_for_points()
        if not_found > 1:
            return [DOMAIN + quote(self.original.first_answer + ' date'),
                    DOMAIN + quote(self.original.second_answer + ' date'),
                    DOMAIN + quote(self.original.third_answer + ' date'),
                    ]
        else:
            return [DOMAIN + quote('prima {} invezione anno'.format(self.original.first_answer)),
                    DOMAIN + quote('prima {} invezione anno'.format(self.original.second_answer)),
                    DOMAIN + quote('prima {} invezione anno'.format(self.original.third_answer))
                    ]

    def get_points_from_texts(self, html: str):
        soup = BeautifulSoup(html, 'lxml')
        if soup.find('div', {'class': 'Z0LcW'}):
            try:
                date_str = soup.find('div', {'class': 'Z0LcW'}).text
                d = parse(date_str)
                return d.year
            except Exception:
                all_texts = [s.find_all(text=True) for s in soup.find_all('span')] + [s.find_all(text=True) for s in
                                                                                      soup.find_all('h3')]
                all_texts_to_string = ' '.join(list(itertools.chain.from_iterable(all_texts)))
                reg = re.findall(r'(\d{4})', all_texts_to_string)
                c = Counter(reg)
                return int(max(c, key=c.get))
        else:
            try:
                text = soup.find('span', {'class': 'e24Kjd'}).text
                reg = re.search(r'(\d{4})', text)
                year = int(reg.group(0)) if reg else sys.maxsize
                return year
            except Exception as _:
                all_texts = [s.find_all(text=True) for s in soup.find_all('span')] + [s.find_all(text=True) for s in
                                                                                      soup.find_all('h3')]
                all_texts_to_string = ' '.join(list(itertools.chain.from_iterable(all_texts)))
                reg = re.findall(r'(\d{4})', all_texts_to_string)
                c = Counter(reg)
                return int(max(c, key=c.get))

    def select_points(self, dates: Dict):
        return {
            self.copy.first_answer: dates[0],
            self.copy.second_answer: dates[1],
            self.copy.third_answer: dates[2]
        }
