import json
from providers.meilisearch_client import Meilisearch
from services.meilisearch_query_service import MeilisearchQueryService
import asyncio

# singleton
class SearchRecipe():

    _instance = None
    _recipes  = {}
    meilisearch_client = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # load values from csv just once
            cls._instance = super(SearchRecipe, cls).__new__(cls)
            rows = []
            with open("food_details/recipes.jsonl", 'r', encoding='utf-8') as f:
                rows = [json.loads(line) for line in f]
            for row in rows:
                recipe_id = row.get('recipe_id')
                cls._recipes[recipe_id] = row

        return cls._instance

    def __init__(self):
        self.meilisearch_client = Meilisearch()

    async def search(self, input, filter_data={}):
        final_results = []
        try:

            if filter_data:
                filter_data = MeilisearchQueryService(filter_data).create_query_search_recipe()

            filter_data['limit'] = 30
            repsonse_search = self.meilisearch_client.search_recipe(input, filter_data)

            for recipe in repsonse_search:
                id = recipe.get('id', None)
                if id == None:
                    continue
                detailed_recipe = self._recipes[id]
                if detailed_recipe:
                    final_results.append(detailed_recipe)

            return {'is_resolved': True, 'data': final_results}
        except Exception as e:
            print(e)
            return {'is_resolved': False, 'err': str(e)}



# python -m services.search_recipe_service

# result = asyncio.run(SearchRecipe().search("",
    # {
    #     'carbohydrate': {
    #         'minValue': 0
    #     },
    #     'protein': {
    #         'maxValue': 1000
    #     }
    # }
# ))
# result = result.get('data')
# print(len(result))