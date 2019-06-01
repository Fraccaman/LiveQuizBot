import os
import time

import spacy

nlp = spacy.load("it_core_news_sm")


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            if False:
                print('%r  %2.2f ms' %
                      (method.__name__, (te - ts) * 1000))
        return result

    return timed


def files(path: str):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            files.append(os.path.join(r, file))
    return files


def ner_extractor(text: str):
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]
