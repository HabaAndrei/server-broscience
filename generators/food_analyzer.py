from providers.openai_client import Openai
from providers.schemas import FoodGeneralDetails, IngredientsDetails
from utils.diverse import sum_ingredients

openai_client = Openai()

class FoodAnalyzer:

    async def analyze_image(self, image:str):
        result_general_details = await self.get_general_details(image)

        is_food = result_general_details.get('data', {}).get('is_food', False)
        if result_general_details.get('is_resolved', False) == False or is_food == False:
            return result_general_details

        general_details = result_general_details.get('data', {})
        ingredients = general_details.get('ingredients', {})
        if len(ingredients) <= 0:
            return result_general_details


        result_ingredients_details = await self.get_ingredients_details(ingredients)
        if result_ingredients_details.get('is_resolved', False) == False:
            return result_ingredients_details

        ingredients_data = result_ingredients_details.get('data')
        ingredients_data = ingredients_data.dict()
        ingredients_details = ingredients_data.get('ingredients')

        total_calories = sum_ingredients(ingredients_details, 'calories')
        total_protein = sum_ingredients(ingredients_details, 'protein')
        total_carbs = sum_ingredients(ingredients_details, 'carbs')
        total_fats = sum_ingredients(ingredients_details, 'fats')
        total_quantity = sum_ingredients(ingredients, 'quantity')


        print(general_details.get('ingredients'), ' <<<<<<<====== general_details.get.ingredients')

        print(ingredients_details, ' <<<<<<<====== ingredients_details')


        final_ingredients = []
        for ingredient in  general_details.get('ingredients'):
            ingredient_name = ingredient.get('name')
            quantity = ingredient.get('quantity')
            for ingredient_details in ingredients_details:
                ingredient_detail_name = ingredient_details.get('name')
                calories = ingredient_details.get('calories')
                protein = ingredient_details.get('protein')
                carbs = ingredient_details.get('carbs')
                fats = ingredient_details.get('fats')

                if ingredient_detail_name == ingredient_name:
                    final_ingredients.append({
                        'name': ingredient_name,
                        'quantity': quantity,
                        'calories': calories,
                        'protein': protein,
                        'carbs': carbs,
                        'fats': fats
                    })

        general_details['ingredients'] = final_ingredients
        general_details['totals'] = {
            'calories': total_calories,
            'protein': total_protein,
            'carbs': total_carbs,
            'fats': total_fats,
            'total_quantity': total_quantity
        }

        return {'is_resolved': True, 'data': general_details}


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

    async def get_ingredients_details(self, ingredients):
        result_details = await openai_client.retry_generate_schema(
            system_prompt='''
                You are a nutrition analysis AI. You receive a list of food ingredients, each with an approximate weight in grams.
                For each food item, you must:
                    1. Identify the ingredints from input
                    2. Estimate the following nutritional values (per total given weight) for each ingredient in part:
                        - Calories (kcal)
                        - Protein (g)
                        - Carbohydrates (g)
                        - Fat (g)
                For each ingredient, estimate the following based on the exact weight provided, using data from authoritative sources (e.g., USDA FoodData Central, EFSA, FAO/INFOODS).
                Be precise, transparent, and rigorous. Your goal is to provide the most accurate, scientifically grounded nutritional analysis possible.
            ''',
            user_prompt=f'''
                Here is a list of food items with approximate weights: {ingredients}
                Please provide their nutritional values in the specified JSON format.
            ''',
            json_schema=IngredientsDetails,
            model='gpt-4.1'
        )
        return result_details