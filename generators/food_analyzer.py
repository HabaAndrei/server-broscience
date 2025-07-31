from providers.openai_client import Openai
from providers.schemas import FoodGeneralDetails, Nutrients
import concurrent.futures
import asyncio

openai_client = Openai()

class FoodAnalyzer:

    # Main function that manages all functionalities for analyzing food images
    async def analyze_image(self, image:str):
        # First, we get the general details of the food
        result_general_details = await self.get_general_details(image)

        # If the image does not contain food, we stop further analysis
        is_food = result_general_details.get('data', {}).get('is_food', False)
        if result_general_details.get('is_resolved', False) == False or is_food == False:
            return result_general_details

        # Extract general details
        food_name = result_general_details.get('data', {}).get('name')
        total_quantity = result_general_details.get('data', {}).get('total_quantity')
        health_score = result_general_details.get('data', {}).get('health_score')
        ingredients = result_general_details.get('data').get('ingredients', {})

        # Get nutrient details for each ingredient
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

    # Search for an ingredient by name in a list of ingredient dictionaries
    def find_ingredient(self, list_of_directories, ingredient_name):
        for directory in list_of_directories:
            if directory.get('name') == ingredient_name:
                return directory

    # Calculate the nutrient value based on the given quantity
    def get_quantity_value(self, quantity=0, value_100=0):
        one_item = value_100 / 100
        return int(quantity * one_item)

    # Get nutrient details for a list of ingredients
    async def get_ingredients_details(self, ingredients):
        loop = asyncio.get_running_loop()
        results = []

        # Execute nutrient requests concurrently to save time
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

        # Process the responses
        for result in results:
            if result.get('is_resolved') == False:
                return result
            data_nutrients = result.get('data')
            ingredient_name = data_nutrients.get('name')
            general_details = self.find_ingredient(ingredients, ingredient_name)
            quantity = general_details.get('quantity')
            calories_per_100 = data_nutrients.get('calories')
            protein_per_100 = data_nutrients.get('protein')
            carbs_per_100 = data_nutrients.get('carbohydrate')
            fats_per_100 = data_nutrients.get('fat')

            # Calculate nutrient values for the specific quantity
            calories = self.get_quantity_value(quantity=quantity, value_100=calories_per_100)
            protein = self.get_quantity_value(quantity=quantity, value_100=protein_per_100)
            carbohydrate = self.get_quantity_value(quantity=quantity, value_100=carbs_per_100)
            fat = self.get_quantity_value(quantity=quantity, value_100=fats_per_100)

            # Update the total values
            total_calories += calories
            total_protein += protein
            total_carbs += carbohydrate
            total_fats += fat
            total_quantity += quantity

            # Add ingredient details to the list
            ingredients_details.append({
                'name': ingredient_name,
                'calories': calories,
                'protein': protein,
                'carbohydrate': carbohydrate,
                'fat': fat,
                'quantity': quantity
            })

        totals = {
            'calories': total_calories,
            'protein': total_protein,
            'carbohydrate': total_carbs,
            'fat': total_fats,
            'total_quantity': total_quantity
        }
        return {'is_resolved': True, 'data': {'totals': totals, 'ingredients': ingredients_details}}

    async def get_general_details(self, image:str):
        result = await openai_client.analyze_image(
            system_prompt='''
                You are an expert in food analysis. Based on the uploaded image, return the structured nutritional info of the meal using the provided JSON schema.
                For each ingredient, specify the approximate cooking method used (e.g., raw, fried, boiled). Be realistic and avoid guessing if uncertain.
                Provide the total quantity of the food and the quantity for each ingredient. The sum of all ingredient quantities must equal the total quantity.
                Important: If the image does not contain food, return the JSON schema with all properties set to null, except for the is_food property, which should be set to false.
            ''',
            user_prompt='''
                Here is an image of a meal. Please analyze it and provide structured data according to the provided JSON schema.
                For each ingredient, include its name, estimated quantity in grams, and the cooking method used (choose from: raw, boiled, fried, baked, grilled, steamed, roasted).
                Be as accurate as possible based on the visual cues in the image. Do not invent ingredients that are not visible.
            ''',
            image=image,
            json_schema=FoodGeneralDetails
        )
        return result

    # Get the nutrients for a specific ingredient
    def get_nutrients(self, ingredient):
        full_name = 'Name: ' + ingredient.get('name') + ', prepared: ' + ingredient.get('preparation')

        result_details = asyncio.run(openai_client.retry_generate_schema(
            system_prompt = '''
                You are a nutrition analysis expert. Your task is to return the nutrient composition for 100 grams of a given ingredient.
                For each ingredient, provide values per 100 grams for:
                    - Calories (kcal)
                    - Protein (g)
                    - Carbohydrates (g)
                    - Fat (g)

                Use authoritative sources such as USDA FoodData Central, EFSA, and FAO/INFOODS.
                Be precise, transparent, and rigorous. Your goal is to deliver the most accurate and scientifically grounded nutritional analysis possible.
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
        # Add the ingredient name to the final response
        result_dict['name'] = ingredient.get('name')
        return {'is_resolved': True, 'data': result_dict}