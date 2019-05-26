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
        return [DOMAIN + self.copy.first_answer + ' date',
                DOMAIN + self.copy.second_answer + ' date',
                DOMAIN + self.copy.third_answer + ' date'
                ]

    def get_points_from_texts(self, html: str):
        soup = BeautifulSoup(html, features="html.parser")
        date_str = soup.find('div', {'class': 'Z0LcW'}).text
        d  = parse(date_str).timestamp()
        return int(d)

    def select_points(self, followers: Dict):
        return {
            self.copy.first_answer: followers[0],
            self.copy.second_answer: followers[1],
            self.copy.third_answer: followers[2]
        }
