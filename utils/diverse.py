def sum_ingredients(ingredients, key):
    n = 0
    for ingredient in ingredients:
        n += ingredient[key]
    return n


def is_number(value):
    """
    Check if the value is an int, float, or numeric string.
    Returns True if it's numeric, otherwise False.
    """
    if isinstance(value, (int, float)):
        return True

    if isinstance(value, str):
        try:
            float(value)  # If it can be converted to float, it's numeric
            return True
        except ValueError:
            return False

    return False

def to_integer(value):
        """
        Convert a float, int, or numeric string to an integer.
        If value is float, it will be truncated (not rounded).
        Raises ValueError if the input is not numeric.
        """
        if not is_number(value):
            raise ValueError("Input must be a number or numeric string.")

        return int(float(value))