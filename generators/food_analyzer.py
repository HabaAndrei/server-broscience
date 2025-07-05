from providers.openai_client import Openai
from providers.schemas import FoodGeneralDetails, Nutrients
import concurrent.futures
import asyncio

openai_client = Openai()

class FoodAnalyzer:

    async def analyze_image(self, image:str):
        result_general_details = await self.get_general_details(image)

        is_food = result_general_details.get('data', {}).get('is_food', False)
        if result_general_details.get('is_resolved', False) == False or is_food == False:
            return result_general_details

        food_name = result_general_details.get('data', {}).get('name')
        total_quantity = result_general_details.get('data', {}).get('total_quantity')
        health_score = result_general_details.get('data', {}).get('health_score')
        ingredients = result_general_details.get('data').get('ingredients', {})

        result_ingredients_details = await self.get_ingredients_details(ingredients)

        if result_ingredients_details.get('is_resolved') == False :
            return result_ingredients_details
        totals = result_ingredients_details.get('data', {}).get('totals')
        ingredients = result_ingredients_details.get('data', {}).get('ingredients')

        return {
            'is_resolved': True,
            'data': {
                'name': food_name,
                'total_quantity': total_quantity,
                'ingredients': ingredients,
                'is_food': is_food,
                'health_score': health_score,
                'totals': totals
            }
        }



    def find_ingredient(self, list_of_directoris, ingredient_name):
        for directory in list_of_directoris:
            if directory.get('name') == ingredient_name:
                return directory

    def get_quantity_value(self, quantity=0, value_100=0):
        one_item = value_100 / 100
        return int(quantity * one_item)

    async def get_ingredients_details(self, ingredients):
        loop = asyncio.get_running_loop()
        results = []
        with concurrent.futures.ThreadPoolExecutor(10) as executor:
            tasks = [
                loop.run_in_executor(executor, self.get_nutrients, ingredient)
                for ingredient in ingredients
            ]
            results = await asyncio.gather(*tasks)

        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        total_quantity = 0

        ingredients_details = []

        for result in results:
            if result.get('is_resolved') == False:
                return result
            data_nutrients = result.get('data')
            ingredient_name = data_nutrients.get('name')
            general_details = self.find_ingredient(ingredients, ingredient_name)
            quantity = general_details.get('quantity')
            calories_per_100 = data_nutrients.get('calories')
            protein_per_100 = data_nutrients.get('protein')
            carbs_per_100 = data_nutrients.get('carbs')
            fats_per_100 = data_nutrients.get('fats')

            calories = self.get_quantity_value(quantity=quantity, value_100=calories_per_100)
            protein = self.get_quantity_value(quantity=quantity, value_100=protein_per_100)
            carbs = self.get_quantity_value(quantity=quantity, value_100=carbs_per_100)
            fats = self.get_quantity_value(quantity=quantity, value_100=fats_per_100)

            total_calories += calories
            total_protein += protein
            total_carbs += carbs
            total_fats += fats
            total_quantity += quantity

            ingredients_details.append({
                'name': ingredient_name,
                'calories': calories,
                'protein': protein,
                'carbs': carbs,
                'fats': fats,
                'quantity': quantity
            })

        totals = {
            'calories': total_calories,
            'protein': total_protein,
            'carbs': total_carbs,
            'fats': total_fats,
            'total_quantity': total_quantity
        }
        return {'is_resolved': True, 'data': {'totals': totals, 'ingredients': ingredients_details}}

    async def get_general_details(self, image:str):
        result = await openai_client.analyze_image(
            system_prompt='''
                You are an expert in food analysis. Based on the uploaded image, return the structured nutritional info of the meal based on the given JSON schema.
                For each ingredient, specify the approximate cooking method used (e.g., raw, fried, boiled). Be realistic and avoid guessing if uncertain.
                You will provide the total quantity of the food, as well as the quantity for each individual ingredient. The sum of all ingredient quantities must equal the total quantity of the food.
                Important: If the image does not contain food, please return the JSON schema with all properties set to null, except for the is_food property, which should be set to false.
            ''',
            user_prompt='''
                 Here is an image of a meal. Please analyze it and provide structured data based on the given JSON schema.
                For each ingredient, include its name, estimated quantity in grams, and the cooking method used (one of: raw, boiled, fried, baked, grilled, steamed, roasted).
                Be as accurate as possible based on the visual cues from the image. Do not invent ingredients that are not visible.
            ''',
            image=image,
            json_schema=FoodGeneralDetails
        )
        return result


    def get_nutrients(self, ingredient):
        full_name = 'Name: ' + ingredient.get('name') + ', preparared: ' + ingredient.get('preparation')
        result_details =  asyncio.run(openai_client.retry_generate_schema(
            system_prompt = '''
                You are a nutrition analysis expert. Your task is to return the nutrient composition for 100 grams of a given ingredient.
                For each ingredient, you must provide values per 100 grams for:
                    - Calories (kcal)
                    - Protein (g)
                    - Carbohydrates (g)
                    - Fat (g)

                For the exact weight of the ingredient provided, estimate the nutritional values using data from authoritative sources (e.g., USDA FoodData Central, EFSA, FAO/INFOODS).
                Be precise, transparent, and rigorous. Your goal is to deliver the most accurate, scientifically grounded nutritional analysis possible.
            ''',
            user_prompt = f'''
                Here is the ingredient: {full_name}.
                Please provide its nutritional values in the specified JSON format.
            ''',
            json_schema=Nutrients,
            model='gpt-4o-mini'
        ))
        if result_details.get('is_resolved') == False:
            return result_details
        result_dict = result_details.get('data').dict()
        result_dict['name'] = ingredient.get('name')
        return {'is_resolved': True, 'data': result_dict}