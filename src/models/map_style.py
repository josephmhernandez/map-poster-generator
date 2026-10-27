# from enum import Enum
import logging
import string

# from turtle import width
from src.style_constants import map_style


# class MapStyle(Enum):
#     black_white = 1
#     black_yellow = 2

#     debug_default_map = 99


def get_map_style_specifications(str_style: string):
    if str_style in map_style:
        return map_style[str_style]
    else:
        logging.info("trying to get map style from style_constants.py")
        logging.error(f"No matching map style for {str_style}")
        raise ValueError("No matching map style")

    # if no str_style do basic map style

    # Extract specifications of MapStyle that are needed to create print, and style map
    # returns:
    #   * tile API endpoint
    #   * transparency payload
    #   * text payload
    #   * Border payload

    logging.info("get map style specifications for: " + str_style)

    context = {}

    style = MapStyle[str_style]
    if style == MapStyle.black_white:
        logging.info("black_white map style specified")

    elif style == MapStyle.black_yellow:
        logging.info("black_yellow map style specified")

    elif style == MapStyle.debug_default_map:
        logging.info("debug_default_map map style specified")
        context[
            "api"
        ] = "https://api.maptiler.com/maps/voyager/{z}/{x}/{y}@2x.png?key=PmIF6Ez34ROeDo7jJGuD#"
        context["borders"] = [
            {"width": 15, "color": "#000000"},
            {"width": 30, "color": "#43ff6400"},
            {"width": 30, "color": "#000000"},
            {"width": 100, "color": "#43ff6400"},
        ]

        # TO DO: Make this text an input from the json object.
        # so bump this out of 'map_style' and have an 'optional' tag
        # idk name yet but for text perosnalizations.

        # Uncomment for
        # context['text'] = ["MADHATTER", '- Washington DC -']
        # context['transparency'] = True
    else:
        logging.error("No matching map style")
        raise ValueError("No matching map style")

    return context
