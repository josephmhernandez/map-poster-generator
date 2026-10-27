# Tile Engine donwload, assemble, and print tiles into a large image file

# Input:
# - BBox (EPSG:4326 projected coordinates) [float] size 4
# - Height (inches) of final picture
# - Width (inches) of final picture
# - Size of tiles we want to download (256, 512, 1024)

# Output:
# - Tiff Image of map at high resolution > 300 dpi
from doctest import OutputChecker
from multiprocessing.dummy import Array
from optparse import Option
import sys
from src.engine.transparency_transformer import TransparencyTransformer

from src.models.value_validator import ValueValidator
import settings
import src.engine.engine_status_codes as engine_status_codes
from cgi import print_form
from stringprep import map_table_b2
from turtle import st
from typing import List
from src.models.coord import Coord
from src.engine.downloader import Downloader
from src.engine.assembler import Assembler
from src.models.bbox import Bbox

from src.engine.validator import validate_payload

from src.models.icon import Icon
from src.models.map import Map
from src.models.pin import Pin
from src.models.print_format import PrintFormat
from src.models.border_style import Border

import logging
import json
from schema import Schema, And, Use, Optional, SchemaError
import settings
import src.engine.engine_utils as engine_utils
import PIL.Image

import PIL.Image as Image

from src.style_constants import TRANSPARENT_TILE_LAYERS


def run_tile_engine(context, verbose=False) -> int:
    """
    context: contents of the poster payload
    verbose: flag, print images after each step to assembler_verbose/ for debugging
    context = {}
    verbose = False
    """

    logging.info("starting tile engine...")
    my_id = context["id"]
    settings.IMAGE_FILE_NAME = f"map_{my_id}.png"
    logging.info(f"producing map...{settings.IMAGE_FILE_NAME}")

    logging.info("cleaing temp folder...")

    engine_utils.create_empty_folder(settings.TEMP_OUTPUT_FOLDER)
    engine_utils.create_empty_folder(settings.TEMP_TEXT_OUTPUT_FOLDER)
    engine_utils.create_empty_folder(settings.TEMP_PIN_OUTPUT_FOLDER)
    engine_utils.create_empty_folder(settings.TEMP_TILE_IMAGE_FOLDER)

    # Mobile Check?
    logging.info("running mobile check...")
    if context["is_mobile"]:
        logging.info("BAD CODING: Is Mobile is True")
    # Multiplier for text has to be 23.
    # Zoom Offset for Downloader has to be 4.

    # Run Downloader
    try:
        logging.info("Running Downloader...")
        new_grid = Downloader.generate_tile_lists(context)
    except Exception as e:
        logging.error("Downloader returned an error")
        logging.critical(e, exc_info=True)
        return engine_status_codes.DOWNLOADER_FAILURE

    # Run Assembler (Border, style, wording, etc.)
    logging.info("Running Assembler...")
    try:
        # Assemble map from downlaoded images
        logging.info("Assemble images")
        Assembler.assemble_image(
            folder_path=settings.TEMP_TILE_IMAGE_FOLDER,
            tile_grid=new_grid,
            output_img_name=settings.IMAGE_FILE_NAME,
            verbose=verbose,
        )
    except Exception as e:
        logging.error("Assembler returned an error")
        logging.critical(e, exc_info=True)
        return engine_status_codes.ASSEMBLER_TILES_FAILURE

    # Crop the image to the specific bbox
    logging.info("Croppig downloaded images to bbox display")
    try:
        Assembler.crop_image(
            context["bbox"],
            img_path=settings.IMAGE_FILE_NAME,
            output_path=settings.IMAGE_FILE_NAME,
            zoom=context["zoom"],
            verbose=verbose,
        )
    except Exception as e:
        logging.error("Assembler returned an error")
        logging.critical(e, exc_info=True)
        return engine_status_codes.ASSEMBLER_CROP_BBOX_FAILURE

    # Add pins to map
    logging.info("Add pins to map " + settings.IMAGE_FILE_NAME)
    try:
        if context["pins"] != None:
            logging.info(f"Adding {str(len(context['pins']))} pins to map image")
            Assembler.add_pins_to_map(
                context,
                input_path=settings.IMAGE_FILE_NAME,
                output_path=settings.IMAGE_FILE_NAME,
                verbose=verbose,
            )
        else:
            logging.info("No pins to place on the image")
    except Exception as e:
        logging.error("Assembler returned an error")
        logging.critical(e, exc_info=True)
        return engine_status_codes.ASSEMBLER_ADD_PIN_FAILURE

    logging.info(
        f"Map is fully assembled need to resize to fit print format. Print format is controleld by dpi: {settings.DPI}"
    )

    # Resize the image to fit the print format.
    # We need to resize according to the dpi for the rest of calculation for building the styling.
    try:
        logging.info("Resizing image to fit print format")
        map_img = PIL.Image.open(settings.IMAGE_FILE_NAME)
        resize_width = int(context["mapDimensionsIn"]["map_width"] * settings.DPI)
        resize_height = int(context["mapDimensionsIn"]["map_height"] * settings.DPI)
        size_map_img = map_img.size
        logging.info(f"Image before resize: {size_map_img}")
        logging.info(f"Resizing image to ({resize_width}, {resize_height})")
        logging.info(
            f"want to be close to zero..... resizing info loss: {float(size_map_img[0] / size_map_img[1]) - float(resize_width / resize_height)}"
        )
        map_img = map_img.resize((resize_width, resize_height))
        map_img.save(settings.IMAGE_FILE_NAME)
        if verbose:
            map_img.save(settings.TEMP_RESIZED_OUTPUT)

    except Exception as e:
        logging.error("Assembler returned an error")
        logging.critical(e, exc_info=True)
        return engine_status_codes.MAIN_RESIZE_FAILURE

    # Is the map transparent? Are we adding a Bg image?
    logging.info("Adding background image to map")
    try:
        if context["bgImgCode"]:
            logging.info("Adding background image to map: " + str(context["bgImgCode"]))
            logging.info("Checking that the tile layer is ideal for transparency")

            if context["tileLayer"] not in TRANSPARENT_TILE_LAYERS:
                logging.error(
                    "Tile layer is not ideal for transparency despite having an image code. Continuing without background image"
                )
                # raise Exception(
                #     "Tile layer is not ideal for transparency but there is a bg image code. tileLayer: "
                #     + str(context["tileLayer"])
                #     + " bgImgCode: "
                #     + str(context["bgImgCode"])
                # )
            else:
                TransparencyTransformer.add_background_and_transparency(
                    settings.IMAGE_FILE_NAME,
                    context["bgImgCode"],
                    output_path=settings.IMAGE_FILE_NAME,
                )
    except Exception as e:
        logging.error("TransparencyTransformer returned an error")
        logging.critical(e, exc_info=True)
        return engine_status_codes.TRANSPARENCY_TRANSFORMER_FAILURE

    # Dont remove. Will use this on other map styles in the future
    # Add map style
    # logging.info("adding style to the map " + str(context["map_style"]))
    # try:
    #     if (
    #         "transparency" in context["map_style"]
    #         and context["map_style"]["transparency"] is True
    #     ):
    #         logging.info("Applying transparency effect to map")
    #         Assembler.add_transparency(
    #             img_path=settings.IMAGE_FILE_NAME,
    #             img_output_path=settings.IMAGE_FILE_NAME,
    #             verbose=verbose,
    #         )
    #     else:
    #         logging.info("No transparency applied to map")
    # except Exception as e:
    #     logging.error("Assembler returned an error")
    #     logging.critical(e, exc_info=True)
    #     return engine_status_codes.ASSEMBLER_ADD_STYLE_FAILURE

    # Add text to map
    logging.info("Adding text to the image")

    try:
        if context["hasText"] == True:
            text = {
                "primary": context["textPrimary"],
                "secondary": context["textSecondary"],
                "coordinate": context["textCoordinates"],
            }
            logging.info(f"Adding text {text} to map image")

            # For Text rendering ->
            if context["is_mobile"]:
                logging.info(
                    "BAD CODING: is_mobile is true so we are setting the pixel multiplier to 23 to add the text"
                )
                context["mapDimensionsIn"]["map_pixel_multiplier"] = 23

            Assembler.add_text(
                img_path=settings.IMAGE_FILE_NAME,
                out_path=settings.IMAGE_FILE_NAME,
                text=text,
                frame_size=context["poster_dimension"],
                context=context,
                verbose=verbose,
            )
        else:
            logging.info("No text added to the image")
    except Exception as e:
        logging.error("Assembler returned an error")
        logging.critical(e, exc_info=True)
        return engine_status_codes.ASSEMBLER_ADD_TEXT_FAILURE

    # Add white background to the map.
    logging.info("Adding white background to the image")
    try:
        TransparencyTransformer.add_white_background(
            input_path=settings.IMAGE_FILE_NAME,
            output_path=settings.IMAGE_FILE_NAME,
        )
    except Exception as e:
        logging.error(
            "TransparencyTransformer returned an error while adding a white background to the image"
        )
        logging.critical(e, exc_info=True)
        return engine_status_codes.TRANSPARENCY_TRANSFORMER_FAILURE

    # We want to save the map in an EPS format.
    im = Image.open(settings.IMAGE_FILE_NAME)
    fig = im.convert("RGB")

    # Convert to CMYK
    jpg = fig.convert("CMYK")
    jpg_file_name = settings.IMAGE_FILE_NAME.replace(".png", ".jpg")
    jpg.save(jpg_file_name)

    new_file_name = settings.IMAGE_FILE_NAME.replace(".png", ".eps")
    fig.save(new_file_name, lossless=True)

    # No borders right now  We are doing flush maps.

    # Add map border
    # logging.info("adding border to map")
    # try:
    #     Assembler.add_border(
    #         borders=context["stylingSpecs"]["borders"],
    #         input_path=settings.IMAGE_FILE_NAME,
    #         output_path=settings.IMAGE_FILE_NAME,
    #         hasText=context["hasText"],
    #         verbose=verbose,
    #     )

    #     # if context["hasText"] == False:
    #     #     Assembler.add_border(
    #     #         borders=context["stylingSpecs"]["borders"],
    #     #         input_path=settings.IMAGE_FILE_NAME,
    #     #         output_path=settings.IMAGE_FILE_NAME,
    #     #         verbose=verbose,
    #     #     )

    # except Exception as e:
    #     logging.error("Assembler returned an error")
    #     logging.critical(e, exc_info=True)
    #     return engine_status_codes.ASSEMBLER_ADD_BORDER_FAILURE

    logging.info("Tile engine completed successfully")
    return engine_status_codes.ENGINE_SUCCESS


def adjust_pil_settings():
    # Increase PIL image size limit
    PIL.Image.MAX_IMAGE_PIXELS = 178956969


def main(args, verbose=False) -> int:
    # Return engine tile code.
    # Set up logger
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        # TO DO: make this a command line argument
        # filename=settings.LOG_FILENAME,
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Validate payload
    logging.info("Validating payload...")
    context = validate_payload(args)

    # Run tile engine
    logging.info("Running tile engine...")
    # To change this output as a string you need to add a json convertor to Bbox and Coordinate and other DTOs that don't allow json.dump method on them.
    logging.info(f"tile-engine context: {str(context)} ")
    adjust_pil_settings()
    engine_code = run_tile_engine(context, verbose=verbose)
    return engine_code


if __name__ == "__main__":
    """
    input: .json file for input_job_payload. TO DO: Specifications for input job payload
    output:
        success:
            engine_status_code
            output_file_path location of final image
        failure:
            error_message
            engine_status_code
            logs_location

    """
    print("starting...")
    try:
        code = main(sys.argv, verbose=False)
        logging.info("finished with Engine result code " + str(code))
    except Exception as e:
        # Maybe this will always run?
        logging.critical(e, exc_info=True)
        sys.exit(engine_status_codes.ENGINE_FAILURE_CRITICAL)

    # Assembler.add_transparency("final_image.png")
    # print('starting border...')

    # Assembler.add_pins_to_map

    # Assembler.add_text(img_path='out.png',out_path='out_text.png', msg=["MADHATTER", '- Washington DC -'])

    # context={}
    # context['api'] = "https://api.maptiler.com/maps/voyager/{z}/{x}/{y}@2x.png?key=PmIF6Ez34ROeDo7jJGuD#"
    # context['borders'] = [
    #     {'width':15, 'color':'#000000'},
    #     {'width':30, 'color':'#43ff6400'},
    #     {'width':30, 'color':'#000000'},
    #     {'width':100, 'color':'#43ff6400'}
    # ]
    # Assembler.add_border(map_style=context, input_path='out_text.png', output_path='out_border.png')

    # 1. Use BBox & size of tiles to get the List of tiles we want to download
    # 2. Multi threaded download of tiles
    # 3. Assemble tiles on download completion
    # 4. Output tiff / Download tiff to device / store tiff somewhere?

    # bbox = [-77.09690093994142,38.86042928143244,-76.97673797607423,38.95393580081098]

    ### USE THIS BBOX.
    # tile_size = 0
    # # 1024 tiles.
    # base_url = 'https://api.maptiler.com/maps/voyager/{z}/{x}/{y}@2x.png?key=msqCXSKnPannMXvUCPsn#'

    # zoom = 15

    # bbox = [-77.07801818847658,38.859092581794336,-76.99562072753908,38.95527071579662]

    # ### USE THIS BBOX.
    # map_box = Bbox(Coord(bbox[0], bbox[3]), Coord(bbox[2], bbox[1]))

    # new_grid = Downloader.generate_tile_lists(map_box, tile_size, base_url, zoom)
    # print('new_grid')
    # print(new_grid)
    # Assembler.assemble_image('./src/tile_images/', new_grid, 'downloaded_image')

    # Assembler.crop_image(map_box, './downloaded_image.png', output_path="./cropped_image.png", zoom=zoom)

    # pin_1 = Pin(icon = Icon.HEART, location=Coord(-77.0369, 38.9072), digital_width=100, digital_height=100, color="hexCode")

    # map = Map(
    #     map_box=map_box,
    #     tile_url=base_url,
    #     print_format=PrintFormat.Canvas_24_36,
    #     pins = pin_1,
    #     border_style=None,
    #     file_path="./cropped_image.png"
    #     )
    # Assembler.add_pin(map,'./w_the_pin.png', pin=pin_1)

    # # Test out border feature
    # Assembler.add_border(in_img,
    #         output_image='butterfly_border_indianred.jpg',
    #         border=100,
    #         color='indianred')

    # input_img = "w_the_pin.png"
    # output_img = "w_border_pin.png"

    # b1 = Border( width=100, color="#FF0000")
    # b21 = Border( width=1000, color="#0000FF")
    # b2 = Border( width=1000, color="#43ff6400")
    # b3 = Border( width=2000, color="#FF0000")
    # borders = [b1, b2, b3]
    # Assembler.add_border(input_path=input_img, output_path=output_img, borders=borders)
