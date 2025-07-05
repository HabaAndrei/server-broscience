from fuzzywuzzy import process
import pandas as pd

# singleton
class SearchFood():

    _instance = None
    _choices = []
    _food  = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # load values from csv just once
            cls._instance = super(SearchFood, cls).__new__(cls)
            df = pd.read_csv('food.csv')
            for ix, row in df.iterrows():
                cls._choices.append(row.get('name'))
                cls._food[row.get('name')] = {
                    'name': row.get('name'),
                    'calories': row.get('calories'),
                    'fats': row.get('fats'),
                    'carbs': row.get('carbs'),
                    'protein': row.get('protein'),
                }

        return cls._instance

    def search(self, input):
        final_results = []
        try:
            results = process.extract(input, SearchFood._choices, limit=15)
            for name in results:
                final_results.append(name[0])
            return {'is_resolved': True, 'data': final_results}
        except Exception as e:
            print(e)
            return {'is_resolved': False, 'err': str(e)}