import re
import sys
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
                return 10000 * d.year + 100 * d.month + 1 * d.day
            except Exception:
                return sys.maxsize
        else:
            try:
                text = soup.find('span', {'class': 'e24Kjd'}).text
                reg = re.search(r'(\d{4})', text)
                year = int(reg.group(0)) if reg else sys.maxsize
                return year
            except Exception as _:
                return sys.maxsize

    def select_points(self, dates: Dict):
        return {
            self.copy.first_answer: dates[0],
            self.copy.second_answer: dates[1],
            self.copy.third_answer: dates[2]
        }
