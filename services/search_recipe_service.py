import json
from providers.meilisearch_client import Meilisearch

# singleton
class SearchRecipe():

    _instance = None
    _choices = []
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

    def search(self, input, filter_data=None):
        repsonse_search = self.meilisearch_client.search_recipe(input, filter_data)
        print(repsonse_search)


# 'id': '53915679', 'name': 'Apple Pumpkin Muffins', 'recipe_description': 'Vegan baked goods, perfect as grab-and-go breakfast.', 'carbohydrate': 40, 'fat': 2, 'protein': 4, 'calories': 200

# python -m services.search_recipe_service

result = SearchRecipe().search("apple", {
#   'filter': 'carbohydrate >= 40 AND protein = 14'
})

print(result)