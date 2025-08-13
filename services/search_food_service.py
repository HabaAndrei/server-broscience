from providers.meilisearch_client import Meilisearch
import json
import time
from utils.diverse import to_integer, is_number
import asyncio

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

    def validate_transform_food(self, food: dict) -> dict:
        servings = food.get('servings', [])
        if not servings:
            return food
        serving = servings[0]

        try:
            calories = serving.get('calories')
            carbohydrate = serving.get('carbohydrate')
            fat = serving.get('fat')
            metric_serving_amount = serving.get('metric_serving_amount')
            protein = serving.get('protein')

            values = [calories, carbohydrate, fat, metric_serving_amount, protein]
            for value in values:
                # if is not a number we return false
                if is_number(value) != True:
                    return {'is_resolved': False}
            # make the value an integer
            serving['calories'] = to_integer(calories)
            serving['carbohydrate'] = to_integer(carbohydrate)
            serving['fat'] = to_integer(fat)
            serving['metric_serving_amount'] = to_integer(metric_serving_amount)
            serving['protein'] = to_integer(protein)
            # return the food
            return {'is_resolved': True, 'data': food}
        except Exception as e:
            print(e)
            return {'is_resolved': False, 'err': str(e)}


    async def search(self, input):
        final_results = []
        try:
            result_search = self.meilisearch_client.search_food(input)
            for result in result_search:
                id = result.get('id')
                food = SearchFood._food.get(id)
                food = self.transform_metric_serving_unit_to_grams(food)

                # verify if the food is valid and tranform the values in integer
                result_validation = self.validate_transform_food(food)
                if result_validation.get('is_resolved', False) == False:
                    continue

                validated_food = result_validation.get('data')
                final_results.append(validated_food)
            return {'is_resolved': True, 'data': final_results}
        except Exception as e:
            print(e)
            return {'is_resolved': False, 'err': str(e)}

# python -m services.search_food_service

# print(time.time())
# result = asyncio.run(SearchFood().search("apple"))
# result = result.get('data')
# print(len(result))
# print(time.time())
