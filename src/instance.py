import string
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

from src.costants import BETWEEN_MODE_TERMS, COORD_MODE_TERMS, INSTAGRAM_MODE_TERMS
from src.utlity import ner_extractor, nlp


class SolverType(Enum):
    BETWEEN = 10
    TERZETTO = 20
    COORD = 30
    INSTAGRAM = 40
    SINGLE_NER = 50
    PRIMA = 60
    DEFAULT = 0


@dataclass
class Instance:
    question: str
    first_answer: str
    second_answer: str
    third_answer: str
    solver: SolverType = field(init=False)
    is_negative: bool = field(init=False)
    correct_answer: int = 0
    ner_question: List = field(default_factory=lambda: [])
    ner_first_answer: List = field(default_factory=lambda: [])
    ner_second_answer: List = field(default_factory=lambda: [])
    ner_third_answer: List = field(default_factory=lambda: [])
    is_both: bool = field(init=False)
    indexes: Dict = field(default_factory=lambda: {})

    def __post_init__(self):
        question_lower = self.to_lower('question')
        self.is_negative = 'NON' in self.question

        self.ner_question = ner_extractor(self.question)

        self.ner_first_answer = ner_extractor(self.first_answer)
        self.is_first_complete_ner = len(self.ner_first_answer) > 0 and self.ner_first_answer[0][0] == self.first_answer
        self.ner_second_answer = ner_extractor(self.second_answer)
        self.is_second_complete_ner = len(self.ner_second_answer) > 0 and self.ner_second_answer[0][
            0] == self.second_answer
        self.ner_third_answer = ner_extractor(self.third_answer)
        self.is_third_complete_ner = len(self.ner_third_answer) > 0 and self.ner_third_answer[0][0] == self.third_answer

        # solver type are ordered from less to more important
        solver = SolverType.BETWEEN if any(
            term in question_lower for term in BETWEEN_MODE_TERMS) else SolverType.DEFAULT
        solver = SolverType.TERZETTO if 'terzetto' in question_lower and question_lower.count("\"") == 4 else solver
        solver = SolverType.COORD if any(
            term in question_lower.translate(str.maketrans('', '', string.punctuation)).split(' ') for term in
            COORD_MODE_TERMS) else solver
        solver = SolverType.INSTAGRAM if any(
            term in question_lower.translate(str.maketrans('', '', string.punctuation)).split(' ') for term in
            INSTAGRAM_MODE_TERMS) else solver
        solver = SolverType.SINGLE_NER if question_lower.count("\"") == 2 and len(self.ner_question) == 1 and \
                                          self.ner_question[0][0].lower() not in question_lower.split('"')[
                                              1] and self.ner_question[0][1]  != 'MISC' else solver
        solver = SolverType.PRIMA if 'chi' not in question_lower and 'primo' in question_lower else solver

        if solver == SolverType.PRIMA:
            self.is_negative = True

        # print(self.ner_first_answer, self.is_first_complete_ner)
        # print(self.ner_second_answer, self.is_second_complete_ner)
        # print(self.ner_third_answer, self.is_third_complete_ner)

        # print(solver)

        self.solver = solver

    def to_lower(self, f: str):
        return self.__dict__[f].lower()

    @staticmethod
    def create_instance(question: str, first_answer: str, second_answer: str, third_answer: str):
        return Instance(question, first_answer, second_answer, third_answer)

    def print_question(self):
        print(self.question)

    def __str__(self):
        return '{}, {}, {}, {}'.format(self.question, self.first_answer, self.second_answer, self.third_answer)
