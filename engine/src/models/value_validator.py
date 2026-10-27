from src.models.bbox import Bbox
from src.models.coord import Coord

# from src.models.map_style import get_map_style_specifications
from src.models.pin import Pin
from typing import List
import logging
import json
from src.models.print_format import PrintFormat
from src.style_constants import API_DICT


class ValueValidator:
    @staticmethod
    def extract_valid_bbox_value(bbox_values: str) -> Bbox:
        try:
            # TO DO:
            # Validate Bbox values

            bbox_dict = json.loads(bbox_values)
            logging.debug(f"bbox_dict: {bbox_dict}")
            tl = Coord(
                lon=bbox_dict["_southWest"]["lng"], lat=bbox_dict["_northEast"]["lat"]
            )
            br = Coord(
                lon=bbox_dict["_northEast"]["lng"], lat=bbox_dict["_southWest"]["lat"]
            )

            # # Return Bbox value
            # Keep this for reference now
            # tl = Coord(bbox_values[0], bbox_values[1])
            # br = Coord(bbox_values[2], bbox_values[3])
            context_bbox = Bbox(tl, br)
            return context_bbox
        except:
            raise ValueError("Could not convert bbox_values list to Bbox object")

    @staticmethod
    def extract_valid_map_style_value(map_style: str) -> dict:
        logging.info("extract map style specifications... map_style: " + map_style)
        # TO DO: Make this method call cleaner. pls.
        # rtn_style = get_map_style_specifications(map_style)

        rtn_style = {
            "api": API_DICT[map_style]["url"],
        }

        print("RTN_STYLE::::::: ", rtn_style)

        return rtn_style

    @staticmethod
    def extract_valid_print_dimension_value(print_dimension: str) -> PrintFormat:
        logging.info("extract print dimension")
        try:
            print_format = PrintFormat[print_dimension]
        except Exception as e:
            logging.error(
                "print_dimension couldn't be converted to correct PrintFormat:"
                + print_dimension
            )
            raise e

        return print_format

    @staticmethod
    def extract_valid_pins_value(pins: List[Pin]) -> List[Pin]:
        # TO DO
        #   - Validate each pin value
        #       - Ensure that all coordinate pairs are inside the bbox
        #   - attach a hex color to each map style
        #   - attach location of each pin file path
        # file path, color, coordinate points (lon, lat)
        pass
        # trying to delete this
        # logging.info("Validating pin(s)")
        # rtnPins = []
        # for pin in pins:
        #     t = {}
        #     t["id"] = pin["id"]
        #     t["icon"] = pin["style"]
        #     t["location"] = [pin["position"]["lng"], pin["position"]["lat"]]
        #     t["digital_width"] = pin["size"]
        #     t["digital_height"] = pin["size"]
        #     # TO DO: UI add color to commercejs (UI)
        #     t["color"] = "#000000"
        #     rtnPins.append(t)

        # return rtnPins

    @staticmethod
    def extract_valid_zoom_value(zoom: int) -> int:
        if zoom > 13 or zoom < 4:
            logging.error("zoom is outside range [ ] : " + str(zoom))
            raise ValueError(f"zoom is outside range : 13 < {zoom} < 4")

        return zoom

    @staticmethod
    def extract_valid_text_flag(input_payload: dict) -> bool:

        if (
            input_payload["textPrimary"] != ""
            or input_payload["textSecondary"] != ""
            or input_payload["textCoordinates"] != ""
        ):
            logging.info("Text found in input payload")
            return True
        logging.info("No text found in input payload")
        return False

    # @staticmethod
    # def validate_input_values(input_payload) -> bool:
    #     logging.info("Validating input payload values...")
    #     is_valid_input = True

    #     logging.info("Validating bbox value")
    #     if(not ValueValidator.is_valid_bbox_value(input_payload['bbox'])):
    #         is_valid_input = False
    #         logging.debug("bbox values aren't valid: {}".format(input_payload['bbox']))

    #     if(not ValueValidator.is_valid_map_style_value(input_payload['map_style'])):
    #         is_valid_input = False
    #         logging.debug("map style values aren't valid: {}".format(input_payload['map_style']))

    #     if(not ValueValidator.is_valid_print_dimension_value(input_payload['print_dimension'])):
    #         is_valid_input = False
    #         logging.debug("map dimesnion value isn't valid: {}".format(input_payload['print_dimension']))

    #     if(not ValueValidator.is_valid_pins_value(input_payload['pins'])):
    #         is_valid_input = False
    #         logging.debug("map pins values aren't valid")

    #     return is_valid_input
