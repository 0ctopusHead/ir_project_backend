import os
import pickle
from spellchecker import SpellChecker
import re
from BM25 import BM25
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
from nltk.tokenize import word_tokenize


checker = SpellChecker(language='en')

stored_folder = Path(os.path.abspath('')).parent.parent / "data" / "processed" / "cleaned_df.pkl"
recipe = pickle.load(open(stored_folder, 'rb'))


def preProcess(s):
    s = re.sub(r'[^A-Za-z]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    s = word_tokenize(s)
    text = ' '.join(s)
    return text


class ManualIndexer:
    def __init__(self, recipe_data):
        self.recipe_data = recipe_data
        self.stored_folder = Path(os.path.abspath('')).parent.parent / "data" / "model/"
        self.stored_file = 'manual_indexer.pkl'
        if os.path.isfile(self.stored_folder / self.stored_file):
            with open(self.stored_folder / self.stored_file, 'rb') as f:
                cache_dict = pickle.load(f)
                print(cache_dict)
            self.__dict__.update(cache_dict)
        else:
            self.run_indexer()

    def run_indexer(self):
        text_columns = ['Name', 'RecipeIngredientParts', 'RecipeInstructions']
        self.df = self.recipe_data[text_columns]

        self.tfidf_vectorizer = TfidfVectorizer(preprocessor=preProcess, stop_words=stopwords.words('english'))
        self.bm25 = BM25(self.tfidf_vectorizer)

        self.bm25.fit(self.df.apply(lambda row: ' '.join(row), axis=1))

        with open(self.stored_folder / self.stored_file, 'wb') as f:
            pickle.dump(self.__dict__, f)

    def query(self, q):
        corrected_query = self.spell_corrct(q)
        print(corrected_query)
        return_score_list = self.bm25.transform(corrected_query)
        hit = (return_score_list > 0).sum()
        rank = return_score_list.argsort()[::-1][:hit]
        results = self.df.iloc[rank].copy().reset_index(drop=True)
        results['score'] = return_score_list[rank]
        return results

    def spell_corrct(self, query):
        tokens = word_tokenize(query)
        corrected_tokens = [checker.correction(token) for token in tokens]
        corrected_tokens = [token for token in corrected_tokens if token is not None]  # Filter out None values
        corrected_query = ' '.join(corrected_tokens)
        return corrected_query


if __name__ == '__main__':
    manual_indexer = ManualIndexer(recipe)
    query_res = manual_indexer.query("carrot cake")
    print(query_res)