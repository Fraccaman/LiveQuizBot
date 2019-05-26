import string
from dataclasses import dataclass
from typing import Dict, List

from src.costants import DOMAIN
from src.instance import Instance
from src.parallel_process import parallel_execution
from src.solvers.solver import Solver


@dataclass
class SingleNer(Solver):

    def is_valid_type(self, instance: Instance):
        return self.type == instance.solver

    def _add_indexes(self, f):
        to_clean = self.copy.__dict__[f]
        to_clean = to_clean.lower().replace('ii ', '')
        self.copy.__dict__[f] = to_clean
        if f == self.fields[1]:
            self.copy.indexes[self.copy.__dict__[f]] = 0
        elif f == self.fields[2]:
            self.copy.indexes[self.copy.__dict__[f]] = 1
        elif f == self.fields[3]:
            self.copy.indexes[self.copy.__dict__[f]] = 2

    def clean(self):
        parallel_execution(self.pool, self._add_indexes, self.fields)

    def craft_queries(self):
        subject = self.copy.question.split("\"")[1]
        return [
            DOMAIN + subject + ' "' + self.copy.ner_question[0][0] + '" AND ' + self.copy.first_answer,
            DOMAIN + subject + ' "' + self.copy.ner_question[0][0] + '" AND ' + self.copy.second_answer,
            DOMAIN + subject + ' "' + self.copy.ner_question[0][0] + '" AND ' + self.copy.third_answer
        ]

    def select_points(self, points: List[Dict[str, int]]):
        if list(points[0].values()).count(0) == 2 and not self.copy.is_negative and sum(points[0].values()) > 1:
            total_points = points[0]
        elif list(points[1].values()).count(0) == 2 and self.copy.is_negative and sum(points[1].values()) > 1:
            total_points = points[1]
        else:
            total_points = {k: points[0].get(k, 0) + points[1].get(k, 0) for k in set(points[0]) | set(points[1])}
            total_points = {k: total_points.get(k, 0) + points[2].get(k, 0) for k in set(total_points) | set(points[2])}
        return total_points
