import nltk


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


INPUT_SENTENCE = "Press {}{}ENTER{} to take a screenshot of the question or {}{}q{} to quit:".format(
    Colors.BOLD, Colors.GREEN, Colors.END, Colors.BOLD, Colors.RED, Colors.END)

BASE_SCREENSHOT_FOLDER = "live_screens"

BETWEEN_MODE_TERMS = ['tra quest', 'quale di quest', 'fra questi', 'tra loro', 'seleziona', 'tra i seguenti',
                      'in quale', 'chi tra', 'da che', 'seguenti', 'fra loro']

COORD_MODE_TERMS = ['nord', 'sud', 'ovest', 'est']

COMMA_REMOVE = ['come', 'perche', 'quando', 'chi', 'cosa', 'quale', 'qual']

PRIMA_MODE_TERMS = ['prima', 'primo', 'precedente', 'dopo']

IT_STOP_WORDS = nltk.corpus.stopwords.words('italian') + ['dell', 'indica', 'vera', 'l\'affermazione', 'i', 'la',
                                                          'queste', 'questo', 'questi', 'in', 'quale', 'quali', 'l',
                                                          '’', '\'', '\"', '``', '\'', '`', 'fra', 'l\'', ' d ', 'd\'']

INSTAGRAM_MODE_TERMS = ['instagram', 'ig']

DOMAIN = "https://www.google.it/search?q="

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,it;q=0.8,la;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
