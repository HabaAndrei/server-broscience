import pandas as pd
from providers.meilisearch_client import Meilisearch

# singleton
class SearchFood():

    _instance = None
    _choices = []
    _food  = {}
    meilisearch_client = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # load values from csv just once
            cls._instance = super(SearchFood, cls).__new__(cls)
            df = pd.read_csv('food.csv')
            for ix, row in df.iterrows():
                cls._choices.append(row.get('name'))
                cls._food[row.get('name')] = {
                    'name': row.get('name'),
                    'calories': int(row.get('calories')),
                    'fats': int(row.get('fats')),
                    'carbs': int(row.get('carbs')),
                    'protein': int(row.get('protein')),
                    'quantity': 100,
                }

        return cls._instance

    def __init__(self):
        self.meilisearch_client = Meilisearch()

    def search(self, input):
        final_results = []
        try:
            result_search = self.meilisearch_client.search(input)
            for result in result_search:
                name = result.get('name')
                ingredient = SearchFood._food[name]
                final_results.append(ingredient)
            return {'is_resolved': True, 'data': final_results}
        except Exception as e:
            print(e)
            return {'is_resolved': False, 'err': str(e)}