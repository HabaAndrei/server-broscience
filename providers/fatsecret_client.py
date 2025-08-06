import requests
import json
import asyncio
import concurrent.futures
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, timezone
from providers.firebase_client import FirestoreAdmin
from config import get_settings
import time


class FatSecretAPI:
    TOKEN_COLLECTION = "fatsecret_tokens"
    TOKEN_DOC = "access_token"
    recipe_types = ['Appetizer', 'Soup', 'Main Dish', 'Side Dish', 'Baked', 'Salad and Salad Dressing', 'Sauce and Condiment', 'Dessert', 'Snack', 'Beverage', 'Other', 'Breakfast', 'Lunch']

    def __init__(self):
        settings = get_settings()
        self.db = FirestoreAdmin().db
        self.consumer_key = settings.fatsecret_consumer_key
        self.consumer_secret = settings.fatsecret_consumer_secret
        self.access_token = None

    def _get_token_from_firestore(self):
        doc_ref = self.db.collection(self.TOKEN_COLLECTION).document(self.TOKEN_DOC)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data and 'access_token' in data:
                return data['access_token']
        return None

    def _store_token_in_firestore(self, token):
        self.db.collection(self.TOKEN_COLLECTION).document(self.TOKEN_DOC).set({
            'access_token': token,
        })

    def _fetch_new_token(self):
        token_url = 'https://oauth.fatsecret.com/connect/token'
        data = {'grant_type': 'client_credentials', 'scope': 'premier'}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(
            token_url,
            data=data,
            headers=headers,
            auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        )
        if response.status_code == 200:
            body = response.json()
            token = body.get('access_token')
            self._store_token_in_firestore(token)
            return token
        else:
            raise Exception(f"Failed to fetch token: {response.text}")

    def get_token(self):
        if not self.access_token:
            token = self._get_token_from_firestore()
            if not token:
                token = self._fetch_new_token()
            else:
                # verify if the token is still available or si expired
                repsonse_test = self.test_request(token)
                code = repsonse_test.get('error', {}).get('code')
                # if code is 13, the token is expired
                if code == 13:
                    # create and store new token
                    token = self._fetch_new_token()
            self.access_token = token
        return self.access_token

    def test_request(self, token):
        '''
            This function is making just request just to see the result.
            This helps as to verify if the token is still available or not
        '''
        api_url = "https://platform.fatsecret.com/rest/food-categories/v2"
        response = requests.get(
            api_url,
            headers={'Authorization': f'Bearer {token}'},
            params={'language': 'en', 'format': 'json'}
        )
        return response.json()

    def _headers(self):
        return {'Authorization': f'Bearer {self.get_token()}'}

    def get_food(self, params):
        api_url = 'https://platform.fatsecret.com/rest/v4/foods'
        response = requests.get(api_url, headers=self._headers(), params=params, timeout=10)
        return response.json()

    def get_food_by_id(self, id):
        return self.get_food({
            'method': 'food.get',
            'food_id': id,
            'format': 'json',
            'language': 'en',
            'include_food_images': True,
            'include_food_attributes': True,
            'flag_default_serving': True
        })

    def search_food(self, input_):
        all_foods = []
        api_url = "https://platform.fatsecret.com/rest/foods/search/v1"
        is_food = True
        page = 0

        print("search for: ", input_)

        while is_food:
            response = requests.get(api_url, headers=self._headers(), params={
                'search_expression': input_,
                'max_results': 50,
                'page_number': page,
                'format': 'json',
            })
            foods = response.json().get('foods', {}).get('food', [])
            if foods:
                all_foods += foods
                page += 1
            else:
                is_food = False

        return all_foods

    def write_jsonl_file(self, data, path):
        with open(path, 'a', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')

    def read_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f]

    def get_and_write_categories(self):
        api_url = "https://platform.fatsecret.com/rest/food-categories/v2"
        response = requests.get(api_url, headers=self._headers(), params={'language': 'en', 'format': 'json'})
        food_categories = response.json().get('food_categories', {}).get('food_category')
        self.write_jsonl_file(food_categories, "food_details/categories.jsonl")

    def get_subcategory(self, id):
        api_url = "https://platform.fatsecret.com/rest/food-sub-categories/v2"
        response = requests.get(api_url, headers=self._headers(), params={
            'language': 'en',
            'format': 'json',
            'food_category_id': id
        })
        return response.json().get('food_sub_categories', {}).get('food_sub_category', [])

    def get_and_write_subcategories(self):
        data = []
        categories = self.read_file("food_details/categories.jsonl")
        for category in categories:
            id = category.get("food_category_id")
            subcategories = self.get_subcategory(id)
            data.append({'category_id': id, 'subcategories': subcategories})
        self.write_jsonl_file(data, "food_details/subcategories.jsonl")

    async def get_and_write_general_food_details(self):
        names = []
        subcategories = self.read_file("food_details/subcategories.jsonl")
        for subcategory in subcategories:
            names += subcategory.get('subcategories', [])

        ids = []
        all_foods = []

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(10) as executor:
            tasks = [loop.run_in_executor(executor, self.search_food, name) for name in names]
            results = await asyncio.gather(*tasks)

        for result in results:
            for food in result:
                food_id = food.get("food_id")
                if food_id not in ids:
                    ids.append(food_id)
                    all_foods.append(food)
            self.write_jsonl_file(all_foods, "food_details/general_food_details.jsonl")
            all_foods = []

    def get_and_write_food(self, id):
        print('start for id: ', id)
        food_result = self.get_food_by_id(id)
        print('food_result => ', food_result)
        details = food_result.get('food', {})
        food_type = details.get('food_type')
        servings = details.get('servings', {}).get('serving', [])

        if isinstance(servings, list) and servings:
            servings = [
                serving for serving in servings
                if (food_type == 'Generic' and serving.get('measurement_description') == 'g') or
                   (food_type == 'Brand' and serving.get('measurement_description') == 'serving' and serving.get('metric_serving_unit') == 'g')
            ] or [servings[0]]
        elif isinstance(servings, dict):
            servings = [servings]

        details['servings'] = servings
        self.write_jsonl_file([details], "food_details/foods.jsonl")

    async def get_and_write_detailed_foods(self):
        ids = []
        foods = self.read_file("food_details/general_food_details.jsonl")
        for food in foods:
            ids.append(food.get('food_id'))

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(2) as executor:
            tasks = [loop.run_in_executor(executor, self.get_and_write_food, id) for id in ids]
            await asyncio.gather(*tasks)

    def get_recipe_types(self):
        api_url = "https://platform.fatsecret.com/rest/recipe-types/v2"
        response = requests.get(api_url, headers=self._headers(), params={'language': 'en', 'format': 'json'})
        recipe_types = response.json().get('recipe_types', {}).get('recipe_type', [])
        return recipe_types

    def search_recipes(self, input_):
        all_recipes = []
        api_url = "https://platform.fatsecret.com/rest/recipes/search/v3"
        is_recipe = True
        page = 0

        while is_recipe:
            try:
                response = requests.get(api_url, headers=self._headers(), params={
                    'search_expression': input_,
                    'must_have_images': True,
                    'page_number': page,
                    'max_results': 50,
                    'sort_by': 'oldest',
                    'format': 'json',
                })
                recipes = response.json().get('recipes', {}).get('recipe', [])
                is_error = response.json().get('error', None)
                code = response.json().get('error', {}).get('code', 0)
                # if the token is expired create new token
                if code == 13:
                    self.get_token()

                if is_error:
                    print(response.json())
                    return {'is_resolved': False}
                if recipes:
                    all_recipes += recipes
                    page += 1
                else:
                    is_recipe = False
            except:
                print("searching recipes failed")

        return {'is_resolved': True, 'data': all_recipes}

    def get_and_write_general_recipe_details(self):

        foods = self.read_file("food_details/foods.jsonl")
        food_names = []
        # get only food name that is 'Generic' by id
        for food in foods:
            food_type = food.get('food_type', '')
            food_name = food.get('food_name', '')
            if food_type == 'Generic' and food_name:
                food_names.append(food_name)

        ids = []
        for name in food_names:
            is_resolved = False
            while is_resolved == False:
                print("we are at: ", name)
                recipes_response = self.search_recipes(name)
                if recipes_response.get('is_resolved') == True:
                    is_resolved = True
                else:
                    time.sleep(120)
                    continue

                recipes = recipes_response.get('data')

                print("we have recipes: ", len(recipes))
                if len(recipes):
                    print("first recipe: ", recipes[0])
                else:
                    print("we dont have recipes !!!!! ")
                recipes_to_store = []
                for recipe in recipes:
                    recipe_id = recipe.get('recipe_id', None)

                    # if the id is already in variable, skip the step
                    if recipe_id in ids:
                        continue

                    recipes_to_store.append(recipe)
                    ids.append(recipe_id)

            # store uinque recipes in file for each food name
            if len(recipes_to_store):
                self.write_jsonl_file(recipes_to_store, "food_details/general_details_recipes.jsonl")


# api = FatSecretAPI()


# !! Get recepies steps

# Get recipes general details (Step 1)
# api.get_and_write_general_recipe_details()

# !! Get foods steps

# Get categories (Step 1)
# api.get_and_write_categories()

# # Get subcategories (Step 2)
# api.get_and_write_subcategories()

# # Get general food details (Step 3)
# asyncio.run(api.get_and_write_general_food_details())

# # Get detailed foods (Step 4)
# asyncio.run(api.get_and_write_detailed_foods())