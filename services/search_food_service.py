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


    def oz_to_grams(self, oz: float) -> float:
        """Convert ounces (oz) to grams (g)."""
        GRAMS_PER_OUNCE = 28.3495
        return oz * GRAMS_PER_OUNCE

    def transform_metric_serving_unit_to_grams(self, food: dict) -> dict:
        """
        Transforms 'metric_serving_amount' from oz to grams if needed.

        Args:
            food (dict): A food dictionary containing serving data.

        Returns:
            dict: The updated food dictionary with grams as unit.
        """

        servings = food.get('servings', [])
        if not servings:
            return food

        serving = servings[0]

        if serving.get("metric_serving_unit", "").lower() == "oz":
            try:
                oz_amount = float(serving.get("metric_serving_amount", 0))
                grams = round(self.oz_to_grams(oz_amount), 2)
                serving["metric_serving_amount"] = grams
                serving["metric_serving_unit"] = "g"
            except (ValueError, TypeError):
                pass  # In case conversion fails, do nothing

        return food

    def search(self, input):
        final_results = []
        try:
            result_search = self.meilisearch_client.search(input)
            for result in result_search:
                id = result.get('id')
                food = SearchFood._food.get(id)
                food = self.transform_metric_serving_unit_to_grams(food)
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
