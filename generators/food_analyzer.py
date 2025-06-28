from providers.openai_client import Openai
from providers.schemas import MealIngredients, IngredientDetails
from utils.diverse import sum_ingredients

openai_client = Openai()

class FoodAnalyzer:

    async def analyze_image(self, image:str):
        result_ingredients = await self.get_ingredients(image)

        if result_ingredients.get('is_resolved') == False:
            return result_ingredients

        food_ingredients = result_ingredients.get('data')
        result_ingredient_details = await self.get_ingredient_details(image=image, ingredients=food_ingredients)

        if result_ingredient_details.get('is_resolved') == False:
            return result_ingredient_details

        details_ingredients = result_ingredient_details.get('data').get('ingredients', [])


        total_calories = sum_ingredients(details_ingredients, 'calories')
        total_protein = sum_ingredients(details_ingredients, 'protein')
        total_carbs = sum_ingredients(details_ingredients, 'carbs')
        total_fats = sum_ingredients(details_ingredients, 'fats')

        food_ingredients['ingredients'] = details_ingredients
        food_ingredients['totals'] = {
            'calories': total_calories,
            'protein': total_protein,
            'carbs': total_carbs,
            'fats': total_fats,
        }

        return {'is_resolved': True, 'data': food_ingredients}


    async def get_ingredients(self, image:str):
        result = await openai_client.analyze_image(
            system_prompt='''
                You are an expert in food analysis. Based on the uploaded image, please provide:
                    - The name of the food
                    - A list of ingredients detected in the image
                    - The quantity of the meal from the image in grams
                    - A health score for the food (1-10)
                Please be careful and make sure to include any ingredients that help the food cook properly (in case it is a cooked dish).
                Such as oil, sausage, or other special ingredients that contain fats or other important elements essential to the recipe.
            ''',
            user_prompt="Here is an image of a meal. Please analyze it and provide the details from json schema",
            image=image,
            json_schema=MealIngredients
        )
        return result

    async def get_ingredient_details(self, image='', ingredients={}):

        result = await openai_client.analyze_image(
            system_prompt='''
                You are an expert in food analysis.
                You will receive an image along with details describing a food item.
                These details include the name of the food, a list of all its ingredients, and the quantity (in grams) of the entire dish.
                Your task is to analyze each ingredient individually. For each ingredient, you must provide:
                    * The name of the ingredient
                    * The estimated number of calories per image
                    * The amount of protein (in grams) per image
                    * The amount of carbohydrates (in grams) per image
                    * The amount of fats (in grams) per image
                    * The quantity of ingredient (in grams)
                    * A health score for the ingredient (1-10)
                Use only the ingredients provided; do not add any others.
                When calculating the quantity for each ingredient, be careful, as you will receive only the total quantity of the entire dish.
            ''',
            user_prompt=f"Please provide details about the image, based in this details of the dish: {ingredients}",
            image=image,
            json_schema=IngredientDetails
        )
        return result