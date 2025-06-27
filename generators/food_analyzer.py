from providers.openai_client import Openai
from providers.schemas import Meal

openai_client = Openai()

class FoodAnalyzer:

    async def analyze_image(self, image:str):
        result_nutrients_ingredients = await self.get_nutrients_ingredients(image)
        if result_nutrients_ingredients.get('is_resolved') == False :
            print("the function in not resolved")
        print(result_nutrients_ingredients)
        nutrients_ingredients = result_nutrients_ingredients.get('data')
        result_ingredients_details = await self.get_ingredients_details(image=image, nutrients_ingredients=nutrients_ingredients)
        print('\n\n', result_ingredients_details)

    async def get_nutrients_ingredients(self, image:str):
        result = await openai_client.analyze_image(
            system_prompt='''
                You are an expert in food analysis. Based on the uploaded image, please provide:
                - The name of the food
                - The estimated number of calories
                - The amount of protein (in grams)
                - The amount of carbohydrates (in grams)
                - The amount of fats (in grams)
                - A health score for the food (1-10)
                - A list of ingredients detected in the image
                - The quantity of the meal from the image in grams
                - If in image si a food or not
            ''',
            user_prompt="Here is an image of a meal. Please analyze it and provide the following details: the name of the food, estimated calories, protein (grams), carbs (grams), fats (grams), a health score, and a list of ingredients.",
            image=image,
            json_schema=Meal
        )
        return result

    async def get_ingredients_details(self, image='', nutrients_ingredients={}):
        result = await openai_client.analyze_image(
            system_prompt='''
                You are an expert in food analysis.
                You will receive an image and details about that image that represent a food.
                Based on this details please provide:
                1. For each ingredient received as a parameter:
                    * The name of the ingredient
                    * The estimated number of calories per image
                    * The amount of protein (in grams) per image
                    * The amount of carbohydrates (in grams) per image
                    * The amount of fats (in grams) per image
                    * A health score for the food (1-10) per image
                    * Grams per image
                2. The name of the ingredient should be the names received in 'ingredients' list.
            ''',
            user_prompt=f"Please provide details about this iamge based on this details about the image: {nutrients_ingredients}",
            image=image,
            json_schema=Meal
        )
        return result