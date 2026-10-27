import PIL
from src.models.bbox import Bbox
from src.models.icon import Icon
from src.models.pin import Pin
from src.models.print_format import PrintFormat
import logging
import os
import glob


def get_leaflet_digital_pixel_size(context) -> tuple:
    # Return the size of the digital display. Used to calculate proportion multiplier for digital to print conversion
    mult = context["mapDimensionsIn"]["map_pixel_multiplier"]

    return (
        context["mapDimensionsIn"]["map_width"] * mult,
        context["mapDimensionsIn"]["map_height"] * mult,
    )

    # trying to delete this.

    # # Return the sizes of the digital display. Used to calculate proportion multiplier for digital to print conversion
    # # TO DO: pull these numbers from a properties file later on so we are only updating properties files and not code
    # if pf == PrintFormat.Canvas_24_36:
    #     return (480, 720)
    # elif pf == PrintFormat.Canvas_20_24:
    #     # TO DO: this pixel convrsion.
    #     return (69, 69)
    # else:
    #     # TO DO: Exception / Logging
    #     return (69, 69)


# def get_print_pixel_size(pf: PrintFormat) -> tuple:
#     # Return the size of print dimensions in pixels
#     # TO DO: pull these numbers from a properties file to keep code consistent when changes

#     if pf == PrintFormat.Canvas_24_36:
#         return (7200, 10800)
#     elif pf == PrintFormat.Canvas_20_24:
#         # TO DO: this pixel convrsion.
#         return (69, 69)
#     else:
#         # TO DO: Exception / Logging
#         return (69, 69)
#     pass


# def get_pin_image_path(pin: Pin) -> str:
#     # TO DO: change this to properties file
#     output_path = ""

#     if pin.icon == Icon.CIRCLE:
#         output_path = "create CIRCLE pin path"
#     elif pin.icon == Icon.HEART:
#         output_path = "src/images/pins/heart_pin_500_500.png"
#     else:
#         # Can't find Icon
#         print("cant find icon")

#     return output_path


def get_pin_size(context, pin: Pin, map_dim: tuple) -> tuple:
    # convert from digital pin pixels size to print pin pixels size
    digital_width, digital_height = get_leaflet_digital_pixel_size(context=context)
    print_width, print_height = map_dim

    print("inputs to get_pin_size")
    print("digital_width: " + str(digital_width))
    print("digital_height: " + str(digital_height))
    print("print_width: " + str(print_width))
    print("print_height: " + str(print_height))
    print("pin.digital_width: " + str(pin.digital_width))
    print("pin.digital_height: " + str(pin.digital_height))

    # print_width, print_height = map_dim = get_print_pixel_size(print_format)

    pin_print_width = round((print_width / digital_width) * pin.digital_width)
    pin_print_height = round((print_height / digital_height) * pin.digital_height)

    return (pin_print_width, pin_print_height)


def get_pin_location(
    context,
    pin: Pin,
    map_dim_pixel: tuple,
    # map_box: Bbox, pin: Pin, map_dim_pixel: tuple, print_format: PrintFormat
) -> tuple:
    # Convert digital pin location (lon, lat) to print pin location (pixels)

    map_box = context["bbox"]
    logging.info("map box: " + str(map_box))
    # Check point is in bbox.
    if not map_box.contains(pin.location):
        logging.info("pin not in box")
        logging.info(f"pin not in box location: {pin.location} icon: {pin.icon}")

    # Calculate bbox total x & y values in web mercator units
    total_x_bbox, total_y_bbox = map_box.get_dimensions_web_meractor()

    logging.info("pin: " + str(pin))
    logging.info("pin location: " + str(pin.location))
    pin_x, pin_y = pin.location.get_web_mercator()

    # Calculate the x & y pixel location of pin on print image
    # trying to delete this
    # pf_width, pf_height = get_print_pixel_size(print_format)
    pf_width, pf_height = map_dim_pixel

    x_pixel_location = round(
        abs(((pin_x - map_box.top_left.get_web_mercator_x()) / total_x_bbox) * pf_width)
    )

    y_pixel_location = round(
        abs(
            ((pin_y - map_box.top_left.get_web_mercator_y()) / total_y_bbox) * pf_height
        )
    )

    logging.info("print width: " + str(pf_width) + " height: " + str(pf_height))
    logging.info("\tpixel location before pin image adjustment")
    logging.info(
        "\tpixel location of pin x: "
        + str(x_pixel_location)
        + " y: "
        + str(y_pixel_location)
    )

    # Adjust for where the pin should actually go on print image
    adj_x_pixels = round(
        x_pixel_location - (get_pin_size(context, pin, map_dim_pixel)[0] * 0.5)
    )
    adj_y_pixels = round(
        y_pixel_location - (get_pin_size(context, pin, map_dim_pixel)[1])
    )
    logging.info("pin image location after adjustment")
    logging.info(
        "\tlocation pin image paste x: "
        + str(adj_x_pixels)
        + " y: "
        + str(adj_y_pixels)
    )

    return (adj_x_pixels, adj_y_pixels)


def create_empty_folder(path: str) -> None:
    # Create an empty folder at the path
    # Remove any existing files in the path
    if os.path.isdir(path):
        logging.info(f"folder exists {path}")
        logging.info(f"cleaning folder {path}")
        files = glob.glob(f"{path}*.png")
        for file in files:
            # logging.info("removing file: " + file)
            os.remove(file)
    else:
        logging.info(f"create temp folder: {path}")
        os.mkdir(path)
