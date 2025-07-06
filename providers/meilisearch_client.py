
import meilisearch
from config import get_settings
import pandas as pd

class Meilisearch:

    _instance = None
    _client = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Meilisearch, cls).__new__(cls)
            cls._client = meilisearch.Client(get_settings().meilisearch_url, get_settings().meilisearch_password)
        return cls._instance

    def store_ingredients_names(self):
        if (self.exists_index(get_settings().meilisearch_index)):
            print('exists and we detele it first')
            self.delete_index(get_settings().meilisearch_index)

        data_to_store = []
        df = pd.read_csv('food.csv')
        for ix, row in df.iterrows():
            name = row.get('name')
            # we store only the name of the ingredient
            data_to_store.append({'id': ix, 'name': name})
        return Meilisearch._client.index(get_settings().meilisearch_index).add_documents(data_to_store)

    def exists_index(self, index:str):
        try:
            Meilisearch._client.get_index(index)
            return True
        except:
            return False

    def delete_index(self, index: str):
        return Meilisearch._client.index(index).delete()

    def search(self, input: str):
        result_search = Meilisearch._client.index(get_settings().meilisearch_index).search(input)
        return result_search.get('hits')

    def get_indexes(self):
        results = Meilisearch._client.get_indexes()
        indexes = []
        if results.get('results') is None:
            return indexes
        for result in results.get('results'):
            indexes.append(result.uid)
        return indexes


# store ingredients in index
# Meilisearch().store_ingredients_names()
# python -m providers.meilisearch_client