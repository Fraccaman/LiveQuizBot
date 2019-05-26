# 23.05.2019 -- 3365
import argparse
import json
import os
from multiprocessing.pool import ThreadPool
from shutil import move
import time

from src.costants import BASE_SCREENSHOT_FOLDER, INPUT_SENTENCE
from src.image_to_text import img_to_text
from src.instance import Instance
from src.switch import Switch
from src.utlity import files, timeit


def do_screenshot():
    #Get the current time
    year, month, day, hour = time.strftime("%Y,%m,%d,%H").split(',')

    # Generate the name for today's folder, and the path
    day_folder_name = "{}_{}_{}".format(day, month, year)
    day_folder_path = os.path.join(BASE_SCREENSHOT_FOLDER, day_folder_name)

    # Create the folder does not yet exist
    if not os.path.exists(day_folder_path):
        os.makedirs(day_folder_path)

    # Generate the name for the current file
    # Get all the existing screens, so we append the correct number
    existing_files = os.listdir(day_folder_path)

    # Generate the final path
    full_filename = "{}__{}__{}.png".format(day_folder_name, hour, len(existing_files))
    current_screen_path = os.path.join(day_folder_path, full_filename)

    return os.system("adb exec-out screencap -p > " + current_screen_path), current_screen_path


@timeit
def do_question(pool: ThreadPool, file: str, debug: bool = False):
    instance = img_to_text(file, pool, debug)
    instance.print_question()
    switch = Switch(pool)
    switch.run(instance)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a bootstrap node')
    sp = parser.add_mutually_exclusive_group()
    sp.add_argument('--live', help='Live game', action='store_true')
    sp.add_argument('--test', help='Test screens', action='store_true')
    sp.add_argument('--dump', help='Dump questions', action='store_true')
    sp.add_argument('--test-dump', help='Test dump', action='store_true')
    sp.add_argument('--test-dump-id', help='Test dump', type=int)
    sp.add_argument('--table', help='Test dump', action='store_true')
    args = parser.parse_args()

    pool = ThreadPool(3)

    try:
        if args.live:
            while True:
                key = input(INPUT_SENTENCE)
                if not key:
                    screen, filename = do_screenshot()
                    if screen == 0:
                        do_question(pool, filename)
                if key == 'q':
                    pool.close()
                    pool.join()
        elif args.test:
            for index, file in enumerate(files('test')):
                if file.split('.')[1] == 'jpg' or file.split('.')[1] == 'png':
                    do_question(pool, file, debug=False)
                    key = input()
                    if key == 'y':
                        move(file, 'screenshot/' + file.split('/')[1])
        elif args.dump:
            exists = os.path.isfile('dump.txt')
            questions = []
            if exists:
                with open('dump.txt') as json_file:
                    data = json.load(json_file, strict=False)
                    switch = Switch(pool)
                    for index, file in enumerate(files('screenshot')):
                        if file.split('.')[1] == 'jpg' or file.split('.')[1] == 'png':
                            instance = img_to_text(file, pool, debug=False)
                            point = switch.run(instance)
                            questions.append({
                                'index': index,
                                'question': instance.question,
                                'solver': instance.solver.name,
                                'answers': [
                                    {
                                        'first_answer': instance.first_answer,
                                        'correct': False,
                                        'bot': list(point.keys()).index(instance.first_answer) == 0 and point[instance.first_answer] != 0,
                                        'points': point[instance.first_answer]
                                    },
                                    {
                                        'second_answer': instance.second_answer,
                                        'correct': False,
                                        'bot': list(point.keys()).index(instance.second_answer) == 0 and point[instance.second_answer] != 0,
                                        'points': point[instance.second_answer]
                                    },
                                    {
                                        'third_answer': instance.third_answer,
                                        'correct': False,
                                        'bot': list(point.keys()).index(instance.third_answer) == 0 and point[instance.third_answer] != 0,
                                        'points': point[instance.third_answer]
                                    },
                                ],
                            })
                d = json.dumps(questions)
                with open('dump.txt', 'w') as the_file:
                    the_file.write(d)
        elif args.test_dump:
            with open('dump.txt') as json_file:
                data = json.load(json_file, strict=False)
                switch = Switch(pool)
                for question in data:
                    instance = Instance.create_instance(question['question'], question['answers'][0]['first_answer'], question['answers'][1]['second_answer'], question['answers'][2]['third_answer'])
                    instance.print_question()
                    switch.run(instance)
                    key = input()
        elif args.test_dump_id:
            with open('dump.txt') as json_file:
                data = json.load(json_file, strict=False)
                switch = Switch(pool)
                for question in data:
                    if question['index'] == args.test_dump_id:
                        instance = Instance.create_instance(question['question'], question['answers'][0]['first_answer'], question['answers'][1]['second_answer'], question['answers'][2]['third_answer'])
                        instance.print_question()
                        switch.run(instance)
                        key = input()
    except KeyboardInterrupt as _:
        pool.close()
        pool.join()
        exit(0)
