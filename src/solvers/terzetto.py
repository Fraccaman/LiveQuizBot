from dataclasses import dataclass
from typing import List, Dict

from src.costants import DOMAIN
from src.solvers.solver import Solver


@dataclass
class Terzetto(Solver):

    def is_valid_type(self, instance):
        return self.type == instance.solver

    def craft_queries(self):
        return [
            DOMAIN + self.copy.question.replace('completa terzetto ', '') + ' AND ' + self.copy.first_answer,
            DOMAIN + self.copy.question.replace('completa terzetto ', '') + ' AND ' + self.copy.second_answer,
            DOMAIN + self.copy.question.replace('completa terzetto ', '') + ' AND ' + self.copy.third_answer
        ]

    def select_points(self, points: List[Dict[str, int]]):
        total_points = {k: points[0].get(k, 0) + points[1].get(k, 0) for k in set(points[0]) | set(points[1])}
        total_points = {k: total_points.get(k, 0) + points[2].get(k, 0) for k in set(total_points) | set(points[2])}
        return total_points
