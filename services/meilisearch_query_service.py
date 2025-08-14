class MeilisearchQueryService:
    constructed_filter = ''
    operators = {
        "min_value": ">=",
        "max_value": "<="
    }
    accepted_keys_recipe = ['calories', 'carbohydrate', 'fat', 'protein']
    query_details = {}
    pagination_details = {}

    def __init__(self, query_details: dict, pagination_details: dict = {}):
        self.query_details = query_details
        self.pagination_details = pagination_details

    def add_to_created_query(self, value: str | int | float, type: str, column: str):
        operator = self.operators[type]
        if operator == None:
            raise Exception("We dont have that operator available")
        if len(self.constructed_filter) < 1:
            self.constructed_filter += f'{column} {operator} {value}'
        else:
            self.constructed_filter += f' AND {column} {operator} {value}'


    def create_query_search_recipe(self):
        query_details = self.query_details
        final_result = {}

        for key in query_details:
            details = query_details.get(key, '')
            min_value = details.get("minValue", None)
            max_value = details.get("maxValue", None)
            if key not in self.accepted_keys_recipe:
                raise Exception("We do not suport that key: ", key)
            if min_value:
                self.add_to_created_query(min_value, "min_value", key)
            if max_value:
                self.add_to_created_query(max_value, "max_value", key)


        if self.pagination_details:
            for key in self.pagination_details:
                final_result[key] = self.pagination_details[key]

        final_result['filter'] = self.constructed_filter
        return final_result



# Query example
# query = {
#     "calories": {
#         "minValue": "10",
#         "maxValue": '100'
#     },
#     "protein": {
#         "minValue": "12",
#         "maxValue": '200'
#     },
#     "fat": {
#         "minValue": "30",
#         "maxValue": '300'
#     },
# }

# pagination = {
#     'limit': 10,
#     'offset': 10
# }

# How to call the class
# a = MeilisearchQueryService(query, pagination).create_query_search_recipe()
# print(a)