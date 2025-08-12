import meilisearch
from config import get_settings
import json

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

    def store_food(self):
        """
        Reads food names from a jsonl file ('food.jsonl') and stores them in a Meilisearch index.
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
        # Add the list of ingredients to the Meilisearch index
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

    def search(self, input: str):
        """
        Searches the Meilisearch index for documents matching the input string.
        Returns the list of matching documents ('hits').
        """
        result_search = Meilisearch._client.index(get_settings().meilisearch_food_index).search(input)
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


# store ingredients in index
# Meilisearch().store_food()
# python -m providers.meilisearch_client

# result = Meilisearch().search("Apple")
# print(result)