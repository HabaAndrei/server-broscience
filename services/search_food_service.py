from providers.meilisearch_client import Meilisearch
import json
import time

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
            rows = []
            with open("food_details/foods.jsonl", 'r', encoding='utf-8') as f:
                rows = [json.loads(line) for line in f]
            for row in rows:
                food_id = row.get('food_id')
                cls._food[food_id] = row

        return cls._instance

    def __init__(self):
        self.meilisearch_client = Meilisearch()

    def search(self, input):
        final_results = []
        try:
            result_search = self.meilisearch_client.search(input)
            for result in result_search:
                id = result.get('id')
                food = SearchFood._food.get(id)
                final_results.append(food)
            return {'is_resolved': True, 'data': final_results}
        except Exception as e:
            print(e)
            return {'is_resolved': False, 'err': str(e)}

# python -m services.search_food_service

# print(time.time())
# result = SearchFood().search("apple")
# print(len(result))
# print(time.time())
