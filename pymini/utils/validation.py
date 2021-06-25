from matplotlib import colors
import os
from config import config

valid_types = [
    "float",
    "int",
    "auto",
    "dir",
    "None"
]


def validate(validate_type, value):
    if validate_type is None:
        return True
    if len(validate_type) == 0:
        return True
    types = validate_type.split('/')
    for type in types:
        if type == 'float':
            if is_float(value):
                return True
        elif type == 'int':
            if is_int(value):
                return True
        elif type == 'color':
            if colors.is_color_like(value):
                return True
        # elif type == 'auto':
        #     if (value.casefold()).__eq__("auto".casefold()):
        #         return True
        elif type == "string":
            return True
        elif type == "dir":
            if os.path.isdir(value):
                return True
        elif type == "None":
            if is_na(value):
                return True
        elif type[0] == '[' and type[-1] == ']': #probably can do this better with regex?
            if (value.casefold()).__eq__(type[1:-1].casefold()):
                return True

        else:
            pass
    return False



# def is_auto(s):
#     return (s.casefold()).__eq__("auto".casefold())
#
#
# def is_color(s):
#     return colors.is_color_like(s)


def is_int(s):
    try:
        return s.isnumeric()
    except:
        return False


def is_float(s):
    try:
        float(s)
        return True
    except:
        return False

def is_na(s):
    if s is None:
        return True
    if s == "":
        return True
    for word in config.validation_na:
        if (s.casefold()).__eq__(word.casefold()):
            return True
    return False

def is_auto(s):
    return (s.casefild()).__eq__('auto'.casefold())

