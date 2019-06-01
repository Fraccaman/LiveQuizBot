import sys
from urllib.parse import quote
from dataclasses import dataclass
from typing import Dict

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
        self.clean_for_points()
        return [DOMAIN + quote(self.original.first_answer + ' date'),
                DOMAIN + quote(self.original.second_answer + ' date'),
                DOMAIN + quote(self.original.third_answer + ' date')
                ]

    def get_points_from_texts(self, html: str):
        soup = BeautifulSoup(html, 'lxml')
        try:
            date_str = soup.find('div', {'class': 'Z0LcW'}).text
            d = parse(date_str)
            return 10000 * d.year + 100 * d.month + 1 * d.day
        except Exception:
            return sys.maxsize

    def select_points(self, dates: Dict):
        return {
            self.copy.first_answer: dates[0],
            self.copy.second_answer: dates[1],
            self.copy.third_answer: dates[2]
        }
