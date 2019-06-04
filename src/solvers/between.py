from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import quote

from src.costants import DOMAIN
from src.instance import Instance
from src.solvers.solver import Solver


@dataclass
class Between(Solver):

    def is_valid_type(self, instance: Instance):
        return self.type == instance.solver

    def craft_queries(self):
        return [DOMAIN + quote(self.copy.question),
                DOMAIN + quote(self.copy.question + ' AND ({} OR {} OR {})'.format(self.copy.first_answer,
                                                                                   self.copy.second_answer,
                                                                                   self.copy.third_answer))
                ]

    def select_points(self, points: List[Dict[str, int]]):
        if list(points[0].values()).count(0) == 2 and not self.copy.is_negative and sum(points[0].values()) > 1:
            total_points = points[0]
        elif list(points[1].values()).count(0) == 2 and not self.copy.is_negative and sum(points[1].values()) > 1:
            total_points = points[1]
        else:
            total_points = {k: points[0].get(k, 0) + points[1].get(k, 0) for k in set(points[0]) | set(points[1])}
        return total_points
