from multiprocessing.pool import ThreadPool
from typing import List, Tuple, Any

import PIL
from PIL import Image
from pytesseract import pytesseract

from src.instance import Instance
from src.parallel_process import parallel_execution

QUESTION_BOUNDARIES = lambda w, h: (35, 450, w - 35, h - 1170)
FIRST_ANSWER_BOUNDARIES = lambda w, h, space: (35, 690 + space, w - 120, h - 1050 + space)
SECOND_ANSWER_BOUNDARIES = lambda w, h, space: (35, 910 + space, w - 120, h - 830 + space)
THIRD_ANSWER_BOUNDARIES = lambda w, h, space: (35, 1130 + space, w - 120, h - 610 + space)
SMALL_ANSWER_BOUNDARIES = lambda w, h: (60, 20, 0.2 * w, h - 30)


def question_to_text(img: Image.Image, w: int, h: int, debug: bool) -> Tuple[str, int]:
    question_image = img.crop(QUESTION_BOUNDARIES(w, h))
    if debug: question_image.show()
    question_text = pytesseract.image_to_string(question_image, lang='ita')
    n_of_lines = question_text.count('\n') + 1
    question_text = question_text.replace('\n', ' ')
    n_of_lines_space = (n_of_lines - 1) * 40 + (25 if n_of_lines == 3 else 0)
    if debug: print('The question is: {}'.format(question_text))
    return question_text, n_of_lines_space


def answer_to_text(data: List[Any]) -> str:
    img = data[0]
    boundaries = data[1]
    debug = data[2]
    answer_image = img.crop(boundaries)
    if debug: answer_image.show()
    answer_text = pytesseract.image_to_string(answer_image, lang='ita').replace('\n', ' ')
    if answer_text == "":
        w, h = answer_image.size
        answer_image = answer_image.crop(SMALL_ANSWER_BOUNDARIES(w, h))
        if debug: answer_image.show()
        answer_text = pytesseract.image_to_string(answer_image, lang='ita', config='--psm 6').replace('\n', ' ')
    return answer_text


def answers_to_text(img: Image.Image, w: int, h: int, question_size: int, pool: ThreadPool, debug: bool) -> List[Any]:
    img = img.point(lambda x: 0 if x < 140 else 255)

    res = parallel_execution(pool, answer_to_text, [
        [img, FIRST_ANSWER_BOUNDARIES(w, h, question_size), debug],
        [img, SECOND_ANSWER_BOUNDARIES(w, h, question_size), debug],
        [img, THIRD_ANSWER_BOUNDARIES(w, h, question_size), debug]
    ])
    if debug: print('The answers are: {}, {}, {}'.format(*res, sep=', '))
    return res


def normalize_image(file_path: str):
    img = Image.open(file_path)
    img = img.convert('LA')
    return img.resize((1280, 1920), PIL.Image.ANTIALIAS)


def get_width_height(img: Image.Image) -> Tuple[int, int]:
    return img.size


def img_to_text(file_path: str, pool: ThreadPool, debug: bool) -> Instance:
    img = normalize_image(file_path)

    w, h = img.size
    question_text, question_size = question_to_text(img, w, h, debug)
    answers_text = answers_to_text(img, w, h, question_size, pool, debug)
    return Instance.create_instance(question_text, answers_text[0], answers_text[1], answers_text[2])
