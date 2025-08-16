import meilisearch
from config import get_settings
import json
from utils.diverse import to_integer

# A singleton class that wraps Meilisearch functionality
class Meilisearch:

    # Class-level variables for singleton instance and Meilisearch client
    _instance = None
    _client = None

    def __new__(cls, *args, **kwargs):
        """
        Ensures that only one instance of Meilisearch is created (Singleton pattern).
        Initializes the Meilisearch client with the configured URL and password.
        """
        if not cls._instance:
            cls._instance = super(Meilisearch, cls).__new__(cls)
            # Initialize the Meilisearch client using values from settings
            cls._client = meilisearch.Client(get_settings().meilisearch_url, get_settings().meilisearch_password)
        return cls._instance

    def read_jsonl_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f]

    def store_recipes(self):
        """
        Reads recipes from a jsonl file ('recipes.jsonl') and stores them in a Meilisearch index.
        If the index already exists, it deletes the existing one first to avoid duplication.
        """
        if self.exists_index(get_settings().meilisearch_recipe_index):
            print('Index exists, deleting it first.')
            self.delete_index(get_settings().meilisearch_recipe_index)

        data_to_store = []
        rows = self.read_jsonl_file("food_details/recipes.jsonl")
        for row in rows:
            recipe_id = row.get("recipe_id")
            recipe_name = row.get("recipe_name")
            recipe_description = row.get("recipe_description")
            serving = row.get("serving_sizes", {}).get("serving", None)
            if serving:
                carbohydrate = to_integer(serving.get("carbohydrate", 0))
                fat = to_integer(serving.get("fat", 0))
                protein = to_integer(serving.get("protein", 0))
                calories = to_integer(serving.get("calories", 0))

            ingredinet_names = []
            ingredients = row.get("ingredients", {}).get("ingredient", [])
            for ingredinet in ingredients:
                name = ingredinet.get("food_name")
                if name:
                    ingredinet_names.append(name)

            data_to_store.append({
                'id': recipe_id,
                'name': recipe_name,
                'recipe_description': recipe_description,
                'carbohydrate': carbohydrate,
                'fat': fat,
                'protein': protein,
                'calories': calories,
                'ingredinet_names': ingredinet_names
            })
        # Add the list of recipes to the Meilisearch index
        Meilisearch._client.index(get_settings().meilisearch_recipe_index).add_documents(data_to_store)
        return Meilisearch._client.index(get_settings().meilisearch_recipe_index).update_filterable_attributes([
            'carbohydrate', 'fat', 'protein', 'calories',
        ])

    def store_foods(self):
        """
        Reads food names from a jsonl file ('foods.jsonl') and stores them in a Meilisearch index.
        If the index already exists, it deletes the existing one first to avoid duplication.
        """
        if self.exists_index(get_settings().meilisearch_food_index):
            print('Index exists, deleting it first.')
            self.delete_index(get_settings().meilisearch_food_index)

        data_to_store = []
        rows = self.read_jsonl_file("food_details/foods.jsonl")

        for row in rows:
            food_type = row.get('food_type')
            food_id = row.get('food_id')
            food_name = row.get('food_name')
            if food_type == 'Brand':
                data_to_store.append({
                    'id': food_id,
                    'name': food_name,
                    'brand_name': row.get('brand_name', '')
                })
                continue
            data_to_store.append({'id': food_id, 'name': food_name})
        # Add the list of food to the Meilisearch index
        return Meilisearch._client.index(get_settings().meilisearch_food_index).add_documents(data_to_store)

    def exists_index(self, index: str):
        """
        Checks if a given Meilisearch index exists.
        Returns True if it exists, otherwise False.
        """
        try:
            Meilisearch._client.get_index(index)
            return True
        except:
            # If an error occurs (e.g., index not found), return False
            return False

    def delete_index(self, index: str):
        """
        Deletes the specified Meilisearch index.
        """
        return Meilisearch._client.index(index).delete()

    def search_food(self, input: str):
        """
        Searches the Meilisearch index for documents matching the input string.
        Returns the list of matching documents ('hits').
        """
        result_search = Meilisearch._client.index(get_settings().meilisearch_food_index).search(input)
        return result_search.get('hits')

    def search_recipe(self, input: str, query: dict | None = None):
        """
        Searches the Meilisearch index for documents matching the input string and filter_data.
        Returns the list of matching documents ('hits').
        """
        result_search = Meilisearch._client.index(get_settings().meilisearch_recipe_index).search(input, query)
        return result_search.get('hits')

    def get_indexes(self):
        """
        Retrieves a list of all index names (UIDs) from the Meilisearch server.
        """
        results = Meilisearch._client.get_indexes()
        indexes = []
        if results.get('results') is None:
            return indexes

        # Extract the 'uid' of each index and add it to the list
        for result in results.get('results'):
            indexes.append(result.uid)
        return indexes


# store foods in index
# Meilisearch().store_foods()

# store recipes in index
# Meilisearch().store_recipes()

# python -m providers.meilisearch_client

# result = Meilisearch().search_food("Apple")
# print(result)