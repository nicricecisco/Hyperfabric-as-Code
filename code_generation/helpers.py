import re

def camel_to_screaming_snake(key, make_singular=False):
    # Insert space before each capital letter
    spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', key)
    # Convert to screaming snake case
    screaming_snake = spaced.replace(' ', '_').upper()
    # Management ports is a special case
    if screaming_snake == "MANAGEMENT_PORTS":
        screaming_snake = "MGMT_PORTS"

    # Remove last character to make word singular
    if make_singular:
        screaming_snake = screaming_snake[:-1]
    return screaming_snake
