import logging
from json import load
from re import I
from schema import Schema, And, Use, Optional, SchemaError

from src.models.value_validator import ValueValidator
from src.models.icon import Icon
from src.models.map import Map
from src.models.pin import Pin
from src.models.print_format import PrintFormat
from src.models.border_style import Border


def validate_schema(input_payload_dict: dict):
    err_list = []
    payload_schema = Schema(
        [
            {
                "id": And(Use(str)),
                "orientation": And(Use(str)),
                "textPrimary": And(Use(str)),
                "textSecondary": And(Use(str)),
                "textCoordinates": And(Use(list)),
                "tileLayer": And(Use(str)),
                "bbox": And(Use(str)),
                "zoom": And(Use(int)),
                "size": And(Use(str)),
                "styling": And(Use(str)),
                # TO DO: Add validation to pinList items
                "pinList": And(Use(list)),
                # TO DO: Add validation to styling items
                # "styling_specs": And(Use(dict)),
                "tileZoomOffset": And(Use(int)),
                # TO DO: Add validation to mapDimensionsIn items
                "mapDimensionsIn": And(Use(dict)),
                "text_styling_specs": And(Use(dict)),
                "isTransparentTextBlock": And(Use(bool)),
                # TO DO: Add these to payload from commercejs (UI)
                # "map_style": And(Use(str)),
                # "print_dimension": And(Use(str)),
                Optional("center"): And(Use(list)),
                Optional("description"): And(Use(str)),
                Optional("lineItemId"): And(Use(str)),
                Optional("name"): And(Use(str)),
                Optional("quantity"): And(Use(int)),
                Optional("unitPrice"): And(Use(float)),
                Optional("location"): And(Use(str)),
                Optional("bgImgCode"): And(Use(str)),
            }
        ]
    )

    logging.info("validating schema...")
    try:
        if not payload_schema.validate(input_payload_dict):
            logging.info("Dictionary input doesn't match expected schema")
            err_list.append("Cannot validate dictionary schema")
    except Exception as e:
        logging.debug("Error thrown while validating input payload schema.")
        logging.error(e, exc_info=True)
        err_list.append(str(e))

    return err_list


def validate_json_attributes(input_payload):
    logging.info(f"validating json attributes... {input_payload}")

    # TO DO: FIX THIS ONLY ONE MAP AT A TIME
    input_payload = input_payload[0]

    context = {}
    try:
        context["id"] = input_payload["id"]
        context["orientation"] = input_payload["orientation"]
        context["textPrimary"] = input_payload["textPrimary"]
        context["textSecondary"] = input_payload["textSecondary"]
        context["textCoordinates"] = input_payload["textCoordinates"]
        context["tileLayer"] = input_payload["tileLayer"]
        # context["stylingSpecs"] = input_payload["styling_specs"]
        context["styling"] = input_payload["styling"]
        context["tileZoomOffset"] = int(input_payload["tileZoomOffset"])
        context["mapDimensionsIn"] = input_payload["mapDimensionsIn"]
        context["hasText"] = ValueValidator.extract_valid_text_flag(input_payload)
        context["bbox"] = ValueValidator.extract_valid_bbox_value(input_payload["bbox"])

        context["textStylingSpecs"] = input_payload["text_styling_specs"]
        context["isTransparentTextBlock"] = input_payload["isTransparentTextBlock"]
        # bg image code.
        logging.info("looking for bgImgCode in input_payload")
        if "bgImgCode" in input_payload:
            context["bgImgCode"] = input_payload["bgImgCode"]
        else:
            context["bgImgCode"] = ""
        logging.info("bgImgCode: " + str(context["bgImgCode"]))

        # TO DO: validate each pin in payload
        context["pins"] = input_payload["pinList"]
        context["size"] = input_payload["size"]

        if "demo" in context["size"]:
            context["is_mobile"] = True
        else:
            context["is_mobile"] = False

        if context["is_mobile"]:
            logging.info(
                "BAD CODING: is_mobile is true so we automaticlly set the tileZoomOffset to 4. We will also be setting the mutiplier to 23 before we add text to the map"
            )
            context["tileZoomOffset"] = 4

        logging.info("value of tileZoomOffset: " + str(context["tileZoomOffset"]))

        context["zoom"] = (
            ValueValidator.extract_valid_zoom_value(input_payload["zoom"])
            + context["tileZoomOffset"]
        )

        # TO DO: add map_style to payload from commercejs (UI)
        # if "map_style" not in input_payload:
        #     logging.debug(f"map_style not in input_payload")
        #     raise ValueError("map_style not in input_payload")
        #     # context["map_style"] = ValueValidator.extract_valid_map_style_value("basic")
        # else:
        #     context["map_style"] = ValueValidator.extract_valid_map_style_value(
        #         input_payload["map_style"]
        #     )

        # TO DO: add map_dimesnion to payload from commercejs (UI)
        if "map_dimension" not in input_payload:
            logging.info(f"map_dimension not in input_payload")
            context["map_dimension"] = "_24_36"
            context["poster_dimension"] = "_24_36"
        else:
            context[
                "map_dimension"
            ] = ValueValidator.extract_valid_print_dimension_value(
                input_payload["print_dimension"]
            )
            context["poster_dimesnion"] = "_24_36"

        # Optional Elements
        # if "pins" in input_payload:
        #     context["pins"] = ValueValidator.extract_valid_pins_value(
        #         input_payload["pinList"]
        #     )
        # else:
        #     context["pins"] = None

    except Exception as e:
        logging.error("This is an error that wasn't caught in the ValueValidator...")
        logging.error(e, exc_info=True)
        raise ValueError("This is an error that wasn't caught in the ValueValidator...")
    return context


def validate_payload(args) -> dict:
    # return context obejct for tile-engine
    context = {}
    logging.info("length of args " + str(len(args)))

    if len(args) != 2:
        logging.error("incorrect number of args. Pass input json file name as arg")
        raise AttributeError("Incorrect number of args")

    # Pre Validate input payload
    with open(args[1], "r") as f:
        logging.info("reading json file: " + str(f))
        input_payload = load(f)

        if input_payload == None:
            logging.debug("Input Args are None")
            raise AttributeError("Input Args are None")

        logging.info("Prevalidate payload schema...")
        validation_error_list = validate_schema(input_payload_dict=input_payload)

        if len(validation_error_list) > 0:
            logging.debug("Error list not empty")
            logging.error(
                f"Error(s) validating payload: {str(len(validation_error_list))} errors"
            )
            raise SchemaError(validation_error_list)

    # TO DO:
    #   - Validate BBox values
    #   - Validate map_style as one of the pre-specified styles
    #   - Validate print_dimension as one of the pre-specified print dimensions
    #   - Validate pins

    # Validate values of json attributes
    context = validate_json_attributes(input_payload=input_payload)

    return context
