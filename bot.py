import argparse
import operator
import os
import re
import string
import time
from multiprocessing.pool import ThreadPool

import PIL
import nltk
import requests
import unidecode
from PIL import Image
from bs4 import BeautifulSoup
from pytesseract import pytesseract

SCREENSHOT = 'screenshot.png'
QUESTION_BOUNDARIES = lambda w, h: (35, 450, w - 35, h - 1170)
FIRST_ANSWER_BOUNDARIES = lambda w, h, space: (35, 690 + space, w - 120, h - 1050 + space)
SECOND_ANSWER_BOUNDARIES = lambda w, h, space: (35, 910 + space, w - 120, h - 830 + space)
THIRD_ANSWER_BOUNDARIES = lambda w, h, space: (35, 1130 + space, w - 120, h - 610 + space)

BETWEEN_MODE_TERMS = ['tra quest', 'quale di quest', 'fra questi', 'tra loro', 'seleziona', 'tra i seguenti',
                      'in quale']

DOMAIN = "https://www.google.it/search?q="

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,it;q=0.8,la;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

it_stop_words = nltk.corpus.stopwords.words('italian') + ['dell', 'indica', 'vera', 'l\'affermazione', 'i', 'la',
                                                          'queste', 'questo', 'questi', 'in', 'quale', 'quali', 'l',
                                                          '\'', '\"', '``', '\'', '`', 'fra', 'l\'']


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' %
                  (method.__name__, (te - ts) * 1000))
        return result

    return timed


def clean(text):
    word_tokenized_list = nltk.tokenize.word_tokenize(text)

    word_tokenized_no_punct = [x.lower() for x in word_tokenized_list if x not in string.punctuation]

    word_tokenized_no_punct_no_sw = [x for x in word_tokenized_no_punct if x not in set(it_stop_words + it_stop_words)]

    word_tokenized_no_punct_no_sw_no_apostrophe = [x.split("'") for x in word_tokenized_no_punct_no_sw]
    word_tokenized_no_punct_no_sw_no_apostrophe = [y for x in word_tokenized_no_punct_no_sw_no_apostrophe for y in x]

    return ' '.join(unidecode.unidecode(' '.join(word_tokenized_no_punct_no_sw_no_apostrophe)).split())


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def files(path):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            files.append(os.path.join(r, file))
    return files


def do_screenshot():
    return os.system("adb exec-out screencap -p > " + SCREENSHOT)


def crop_image(img, area):
    return img.crop(area)


def question_image_to_text(img, area):
    question_image = crop_image(img, area)
    question_text = pytesseract.image_to_string(question_image, lang='ita')
    n_of_lines = question_text.count('\n') + 1
    question_text = question_text.replace('\n', ' ')
    n_of_lines_space = (n_of_lines - 1) * 40 + (25 if n_of_lines == 3 else 0)
    return question_text, n_of_lines_space


def answer_image_to_text(data):
    answer_image = crop_image(data[0], data[1])
    answer_text = pytesseract.image_to_string(answer_image, lang='ita').replace('\n', ' ')
    return answer_text


def unpack_texts(texts):
    return texts[0], texts[1], texts[2], texts[3]


def select_modes(question):
    question_lower = question.lower()
    NEGATIVE_MODE = 'NON' in question
    QUERY_MODE = 'BETWEEN' if any(term in question_lower for term in BETWEEN_MODE_TERMS) else 'DEFAULT'
    return NEGATIVE_MODE, QUERY_MODE


def craft_query_google(mode, question, answers):
    if mode == 'BETWEEN':

        return DOMAIN + question + ' AND (' + (answers[0] + ' OR ' if answers[0] != '' else '') + (
            answers[1] + ' OR ' if answers[1] != '' else '') + (
                   answers[2] if answers[2] != '' else '') + ')'
    else:
        return DOMAIN + question


def get_anwer_google(query, question, answers):
    query = query.replace(' ', '+')

    r = requests.get(query, headers=headers)
    soup = BeautifulSoup(r.text, features="html.parser")
    all_links = soup.find_all('div', {'class': 'g'})

    points = {
        answers[0]: 0,
        answers[1]: 0,
        answers[2]: 0
    }

    for link in all_links:
        try:
            title = link.find('div', {'class': 'r'}).find('h3').text.lower()
            description = link.find('div', {'class': 's'}).find('span', {'class': 'st'}).text.lower()
        except Exception as e:
            continue

        for answer in points.keys():
            if answer == ''.strip(): continue
            count_title = 0
            count_description = 0
            c_title = clean(title)
            c_description = clean(description)
            for a in answer.lower().split(' '):
                if a.strip() != '':
                    count_title += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(a), c_title))
            for a in answer.lower().split(' '):
                if a.strip() != '':
                    count_description = + sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(a), c_description))

            points[answer] += count_title + count_description

    return points


def print_results(points, NEGATIVE_MODE):
    if NEGATIVE_MODE:
        res = list(sorted(points.items(), key=operator.itemgetter(1)))
    else:
        res = list(reversed(sorted(points.items(), key=operator.itemgetter(1))))

    print('{}1: {}{} - score: {}'.format(Colors.BOLD, res[0][0].upper(), Colors.END, res[0][1]))
    print('{}2: {}{} - score: {}'.format(Colors.BOLD, res[1][0].upper(), Colors.END, res[1][1]))
    print('{}3: {}{} - score: {}'.format(Colors.BOLD, res[2][0].upper(), Colors.END, res[2][1]))


@timeit
def do_question(pool, file=SCREENSHOT, debug=False):
    img = Image.open(file)
    img = img.convert('LA')
    img = img.resize((1280, 1920), PIL.Image.ANTIALIAS)
    img_a = img.point(lambda x: 0 if x < 140 else 255)

    w, h = img.size
    question_text, space = question_image_to_text(img, QUESTION_BOUNDARIES(w, h))

    answers_text = pool.map(answer_image_to_text, [
        [img_a, FIRST_ANSWER_BOUNDARIES(w, h, space)],
        [img_a, SECOND_ANSWER_BOUNDARIES(w, h, space)],
        [img_a, THIRD_ANSWER_BOUNDARIES(w, h, space)]
    ])
    if debug: print(*[question_text] + answers_text, sep='\n')

    NEGATIVE_MODE, QUERY = select_modes(question_text)

    texts_clean = pool.map(clean, [question_text] + answers_text)
    question_text, first_answer_text, second_answer_text, third_answer_text = unpack_texts(texts_clean)

    query = craft_query_google(QUERY, question_text, [first_answer_text, second_answer_text, third_answer_text])
    points = get_anwer_google(query, question_text, [first_answer_text, second_answer_text, third_answer_text])
    print_results(points, NEGATIVE_MODE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a bootstrap node')
    parser.add_argument('--live', help='Live game', default=False, type=bool)
    parser.add_argument('--test', help='Test screen', default=True, type=bool)
    args = parser.parse_args()

    pool = ThreadPool(3)

    if args.live:
        while True:
            key = input("Press " + Colors.BOLD + Colors.GREEN + "ENTER" + Colors.END + " to take a screenshot" +
                        " of the question or press " + Colors.BOLD + Colors.RED + "q" + Colors.END + " to quit: ")
            if not key:
                screen = do_screenshot()
                if screen == 0:
                    do_question(pool)
            if key == 'q':
                pool.close()
                pool.join()
    elif args.test:
        for file in files('screenshot'):
            do_question(pool, file, debug=True)
            print('\n')

        pool.close()
        pool.join()
