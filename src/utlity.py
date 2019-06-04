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

# def clean(to_clean):
#     to_clean = unidecode(to_clean.lower())
#     word_tokenized_list = nltk.tokenize.word_tokenize(to_clean)
#     word_tokenized_no_punct = [x.lower() for x in word_tokenized_list if x not in string.punctuation]
#     word_tokenized_no_punct_no_sw = [x for x in word_tokenized_no_punct if
#                                      x not in set(IT_STOP_WORDS)]
#     word_tokenized_no_punct_no_sw_no_apostrophe = [x.split("'") for x in word_tokenized_no_punct_no_sw]
#     word_tokenized_no_punct_no_sw_no_apostrophe = [y for x in word_tokenized_no_punct_no_sw_no_apostrophe for y
#                                                    in x]
#     last = [x for x in word_tokenized_no_punct_no_sw_no_apostrophe if
#             x not in set(IT_STOP_WORDS)]
#     return last


# word = "orso polare"
#
# from nltk.corpus import wordnet as wn
# cane_lemmas = wn.lemmas("orso polare", lang="ita")
# if len(cane_lemmas) > 0:
# hypernyms = cane_lemmas[0].synset().hypernyms() if len(cane_lemmas) > 0 else None
# to_search = [word]
#
# syn = hypernyms[0].lemmas(lang="ita")
# for i in syn:
#     n = i.name()
#     print(n)
#     res = wikipedia.search(n)
#     to_search.append(res[0])
#     print(to_search)
#     for i in to_search:
#         print(i, wikipedia.page(i).content.count(' denti '))
