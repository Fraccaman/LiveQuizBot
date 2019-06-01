from dataclasses import dataclass
from typing import List, Dict

from bs4 import BeautifulSoup

from src.parallel_process import parallel_execution
from src.solvers.solver import Solver


@dataclass
class Default(Solver):

    def is_valid_type(self, instance):
        return True

    def get_result_number(self, html):
        soup = BeautifulSoup(html, 'lxml')
        try:
            results_text = soup.find('div', {'id': 'resultStats'}).text
        except Exception as _:
            return 0
        num = results_text.split(' ')[1].replace('’', '').replace(',', '')
        return int(num) if num.isdigit() else 0

    def count_points(self, queries: List[str]):
        res = parallel_execution(self.pool, self.get_page, queries)
        points = parallel_execution(self.pool, self.get_points_from_texts, [res[0]])
        results = parallel_execution(self.pool, self.get_result_number, res[1:])
        point = self.select_points(points)
        if sum(point.values()) == 0:
            keys = point.keys()
            for index, key in enumerate(keys):
                point[key] = results[index]
        return self.print_results(point)