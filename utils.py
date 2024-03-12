import re
from nltk.tokenize import word_tokenize
def preProcess(s):
    s = re.sub(r'[^A-Za-z]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    s = word_tokenize(s)
    text = ' '.join(s)
    return text