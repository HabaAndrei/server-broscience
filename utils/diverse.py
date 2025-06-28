def sum_ingredients(ingredients, key):
    n = 0
    for ingredient in ingredients:
        n += ingredient[key]
    return n