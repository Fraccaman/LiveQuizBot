from dataclasses import dataclass

from bs4 import BeautifulSoup

from src.costants import DOMAIN, COORD_MODE_TERMS
from src.instance import Instance
from src.solvers.solver import Solver


@dataclass
class Coord(Solver):

    def is_valid_type(self, instance: Instance):
        return self.type == instance.solver

    def craft_queries(self):
        if 'stat' in self.copy.question:
            return [DOMAIN + self.copy.first_answer + ' coordinates',
                    DOMAIN + self.copy.second_answer + ' coordinates',
                    DOMAIN + self.copy.third_answer + ' coordinates'
                    ]
        else:
            return [DOMAIN + self.copy.first_answer + ' city coordinates',
                    DOMAIN + self.copy.second_answer + ' city coordinates',
                    DOMAIN + self.copy.third_answer + ' city coordinates'
                    ]

    def get_points_from_texts(self, html: str):
        soup = BeautifulSoup(html, features="html.parser")
        return soup.find('div', {'class', 'Z0LcW'}).text.strip()

    def select_points(self, points):
        return self.get_points_from_coords(points)

    def get_points_from_coords(self, coordinates):
        direction = list(filter(lambda x: x in COORD_MODE_TERMS, self.copy.question.split(' ')))[0]
        south_bucket = []
        east_bucket = []
        north_bucket = []
        west_bucket = []
        answer_dict = {}

        for idx, coordinate in enumerate(coordinates):
            latLong = coordinate.split(', ')
            lat_orientation = latLong[0].split('° ')[1]
            lat_value = float(latLong[0].split('° ')[0])
            lon_orientation = latLong[1].split('° ')[1]
            lon_value = float(latLong[1].split('° ')[0])
            answer_dict[lat_value] = idx
            answer_dict[lon_value] = idx
            if lat_orientation == 'S':
                south_bucket.append(lat_value)
            elif lat_orientation == 'N':
                north_bucket.append(lat_value)
            if lon_orientation == 'W':
                west_bucket.append(lon_value)
            elif lon_orientation == 'E':
                east_bucket.append(lon_value)

        lowest_value = 0
        if direction == 'sud':
            if len(south_bucket) > 0:
                south_bucket.sort(reverse=True)
                lowest_value = south_bucket[0]
            else:
                north_bucket.sort()
                lowest_value = north_bucket[0]
        elif (direction == 'nord'):
            if len(north_bucket) > 0:
                north_bucket.sort(reverse=True)
                lowest_value = north_bucket[0]
            else:
                south_bucket.sort()
                lowest_value = south_bucket[0]
        elif (direction == 'est'):
            if len(east_bucket) > 0:
                east_bucket.sort(reverse=True)
                lowest_value = east_bucket[0]
            else:
                west_bucket.sort()
                lowest_value = west_bucket[0]
        elif (direction == 'ovest'):
            if len(west_bucket) > 0:
                west_bucket.sort(reverse=True)
                lowest_value = west_bucket[0]
            else:
                east_bucket.sort()
                lowest_value = east_bucket[0]

        lowest_answer = answer_dict[lowest_value]

        return {
            self.copy.first_answer: 1 if lowest_answer == 0 else 0,
            self.copy.second_answer: 1 if lowest_answer == 1 else 0,
            self.copy.third_answer: 1 if lowest_answer == 2 else 0,
        }
