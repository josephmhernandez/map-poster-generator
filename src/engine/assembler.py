from cgi import print_form
from cmath import e
import enum
import logging
from tkinter import font
from typing import List
from xml.etree.ElementTree import PI
from PIL import ImageOps, ImageDraw, ImageFont, Image
import math
import decimal
from pyparsing import Regex
from src.models.pin import Pin
import src.engine.engine_utils
from os import listdir
from os.path import isfile, join
from src.models.bbox import Bbox
from src.models.coord import Coord
import mercantile
import numpy as np
from regex import search
from src.models.border_style import Border
import numpy as np
from src.style_constants import map_font_path, map_pin_path
import settings
import re


class Assembler:
    @staticmethod
    def assemble_image(folder_path, tile_grid, output_img_name, verbose=False):
        # Given a folder path, concatenate the map image from these tile images.
        # tile_grid [x, y] Number of tiles in grid
        logging.info("assembling images from " + folder_path)
        logging.info("size of image " + str(tile_grid))
        # Make a list of the image names
        image_files = [folder_path + f for f in listdir(folder_path)]
        # Open the image set using pillow
        images = [Image.open(x) for x in image_files]
        # Calculate the number of image tiles in each direction
        edge_length_x = tile_grid[0]
        edge_length_y = tile_grid[1]
        # Find the final composed image dimensions
        width, height = images[0].size
        total_width = width * edge_length_x
        total_height = height * edge_length_y
        # Create a new blank image we will fill in
        composite = Image.new("RGBA", (total_width, total_height))

        # Loop over the x and y ranges
        y_offset = 0
        for i in range(0, edge_length_x):
            x_offset = 0

            for j in range(0, edge_length_y):
                # Open up the image file and paste it into the composed
                # image at the given offset position
                tmp_img = Image.open(folder_path + str(i) + "." + str(j) + ".png")
                composite.paste(tmp_img, (y_offset, x_offset))
                x_offset += width  # Update the width
            y_offset += height  # Update the height

        # Save the final image
        composite.save("./" + output_img_name)

        if verbose:
            logging.info(f"saving assembled image to {settings.TEMP_OUTPUT_FOLDER}")
            composite.save(settings.TEMP_OUTPUT_FOLDER + "assemble-tiles.png")

        logging.info("output image: " + output_img_name)

    @staticmethod
    def check_image_folder_exists(folder_path):
        # TO DO: Check the existance of folder and process error associated with this.
        print("TO DO: check image folder existance")

    @staticmethod
    def crop_image(map_box, img_path, output_path, zoom, verbose=False):
        logging.info(
            "cropping the image to the correct size. Input: "
            + img_path
            + "; Output: "
            + output_path
        )

        # Open Image
        img = Image.open(img_path)
        img_width, img_height = img.size

        # Create tile_box (it is larger than map box)
        tl_tile = mercantile.tile(
            float(map_box.top_left.lon), float(map_box.top_left.lat), zoom
        )
        br_tile = mercantile.tile(
            float(map_box.bottom_right.lon), float(map_box.bottom_right.lat), zoom
        )
        br_tile = mercantile.Tile(x=br_tile.x + 1, y=br_tile.y + 1, z=zoom)
        tl_coord = Coord(mercantile.ul(tl_tile).lng, mercantile.ul(tl_tile).lat)
        br_coord = Coord(mercantile.ul(br_tile).lng, mercantile.ul(br_tile).lat)
        tile_box = Bbox(tl_coord, br_coord)

        # Get difference between tile_box and map_box
        # .... with web mercantile units
        m_diff_left_degree = abs(
            tile_box.top_left.get_web_mercator_x()
            - map_box.top_left.get_web_mercator_x()
        )
        m_diff_top_degree = abs(
            tile_box.top_left.get_web_mercator_y()
            - map_box.top_left.get_web_mercator_y()
        )
        m_diff_right_degree = abs(
            tile_box.bottom_right.get_web_mercator_x()
            - map_box.bottom_right.get_web_mercator_x()
        )
        m_diff_bottom_degree = abs(
            tile_box.bottom_right.get_web_mercator_y()
            - map_box.bottom_right.get_web_mercator_y()
        )

        # Calculate percent change of diff and convert to pixels
        # .... with web mercantile units
        m_total_x_degree = abs(
            tile_box.top_left.get_web_mercator_x()
            - tile_box.bottom_right.get_web_mercator_x()
        )
        m_total_y_degree = abs(
            tile_box.top_left.get_web_mercator_y()
            - tile_box.bottom_right.get_web_mercator_y()
        )

        # Calculate pixel change
        # .... with web mercantile units
        m_pixel_diff_left = round((m_diff_left_degree / m_total_x_degree) * img.width)
        m_pixel_diff_right = round((m_diff_right_degree / m_total_x_degree) * img.width)
        m_pixel_diff_top = round((m_diff_top_degree / m_total_y_degree) * img.height)
        m_pixel_diff_bottom = round(
            (m_diff_bottom_degree / m_total_y_degree) * img.height
        )

        # Crop Image. Save as output_path
        # ... with web mercantile units
        m_crop_payload = (
            0 + m_pixel_diff_left,
            0 + m_pixel_diff_top,
            img.width - m_pixel_diff_right,
            img.height - m_pixel_diff_bottom,
        )

        im1 = img.crop(m_crop_payload)

        logging.info("Save cropped image to " + output_path)
        if verbose:
            logging.info(f"saving cropped image to {settings.TEMP_OUTPUT_FOLDER}")
            im1.save(settings.TEMP_OUTPUT_FOLDER + "crop-to-bbox.png")
        im1.save(output_path)

    @staticmethod
    def add_pin(
        context,
        input_path: str,
        output_path: str,
        pin: Pin,
        verbose: bool = False,
        id: int = 69,
    ) -> None:
        # Input map path and pin DTO
        # Save map to output location with pin on map
        # logging.info(f"map context: {context}")
        # Open image
        map_img = Image.open(input_path)

        # Make sure map is expected size
        # map_dim = src.engine.engine_utils.get_print_pixel_size(context["map_dimension"])
        # map_img = map_img.resize(map_dim)
        map_dim = map_img.size
        logging.info("current map size: " + str(map_dim))

        # Open Pin image Pin utils
        pin_img = Image.open(map_pin_path[pin.icon])
        # pin_img = Image.open(src.engine.engine_utils.get_pin_image_path(pin))

        # Calculate location of pin on the map based on size of map image (pixels)
        (
            print_pin_location_x,
            print_pin_location_y,
        ) = src.engine.engine_utils.get_pin_location(
            context, pin, map_dim_pixel=map_dim
        )
        # trying to delete this
        #     map_box=context["bbox"],
        #     pin=pin,
        #     map_dim_pixel=map_dim,
        #     print_format=context["size"],
        # )

        logging.info("pin location on print x: " + str(print_pin_location_x))
        logging.info("pin location on print y: " + str(print_pin_location_y))

        # Resize pin image
        new_pin_dim = src.engine.engine_utils.get_pin_size(context, pin, map_dim)
        logging.info("pin pixel size on map " + str(new_pin_dim))
        pin_img = pin_img.resize(new_pin_dim)

        # Place pin image on map
        map_img.paste(
            pin_img, (print_pin_location_x, print_pin_location_y), mask=pin_img
        )
        if verbose:
            logging.info(f"saving map with pin to {settings.TEMP_PIN_OUTPUT_FOLDER}")
            map_img.save(
                settings.TEMP_PIN_OUTPUT_FOLDER + "add-pin-" + str(id) + ".png"
            )

        # Save map with pin saved as " + output_path)
        map_img.save(output_path)

    @staticmethod
    def add_pins_to_map(
        context, input_path: str, output_path: str, verbose: bool = False
    ) -> None:
        id = 0
        for p in context["pins"]:
            print("pin")
            print(p)
            curr_pin = Pin(
                icon=p["style"],
                location=[p["position"]["lng"], p["position"]["lat"]],
                digital_height=p["size"],
                digital_width=p["size"],
                color=p["color"] if "color" in p else "#000000",
            )
            logging.info("adding pin: " + str(curr_pin))
            Assembler.add_pin(
                context,
                input_path=input_path,
                output_path=output_path,
                pin=curr_pin,
                verbose=verbose,
                id=id,
            )
            id += 1

    @staticmethod
    def isHexColor(color: str) -> bool:
        return search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", color)

    @staticmethod
    def add_border(
        borders: list,
        input_path: str,
        output_path: str,
        hasText: bool,
        verbose: bool = False,
    ):
        # If Input path and output path are the same the image will be overwritten
        # border width dimensions in pixels

        # Prepare border payload: width, color. width in pixels, color in hex code

        # fill is color value defined
        # borders = map_style["borders"]
        if len(borders) == 0:
            logging.info("no borders to add to map")
            return

        img = Image.open(input_path).convert("RGBA")

        for border in borders:
            # if isinstance(border.width, int) and Assembler.isHexColor(border.color):
            pix_size = int(settings.DPI * border["border_inches"])
            img = ImageOps.expand(
                img,
                # (e, n, w, s)
                border=(pix_size, pix_size, pix_size, 0),
                fill=border["color"],
            )
            # else:
            # print("hex code doesn't exist" +  str(border.width) + str(border.color))

        # Remove when we have a better way of handling no text on map. Need border payload that's passed from ui.
        if not hasText:
            pix_size = int(settings.DPI * borders[0]["border_inches"])
            img = ImageOps.expand(
                img,
                # (e, n, w, s)
                border=(0, 0, 0, pix_size),
                fill=borders[0]["color"],
            )

        if verbose:
            logging.info(f"saving map with border to {settings.TEMP_OUTPUT_FOLDER}")
            img.save(settings.TEMP_OUTPUT_FOLDER + "add-border.png")
        img.save(output_path)

    @staticmethod
    def add_transparency(img_path: str, img_output_path: str, verbose: bool = False):
        # Transform picture to RGBA
        # calculate range of pixels to loop through and change transparency
        # calculatre the step of each pixel change
        # TO DO: Change .75 and .95 to inputs for fading.
        img = Image.open(img_path).convert("RGBA")

        arr = np.array(img)
        alpha = arr[:, :, 3]
        n = len(alpha)
        alpha[:] = np.interp(
            np.arange(n), [0, 0.75 * n, 0.95 * n, n], [255, 255, 0, 0]
        )[:, np.newaxis]
        img = Image.fromarray(arr, mode="RGBA")
        if verbose:
            logging.info(
                f"saving map with transparency to {settings.TEMP_PIN_OUTPUT_FOLDER}"
            )
            img.save(settings.TEMP_OUTPUT_FOLDER + "add-transparency.png")
        img.save(img_output_path)

    @staticmethod
    def create_image(bgColor, message, font, fontColor, padding):
        """
        Creates an image block with the given message
        """
        W, H = font.getsize(message)

        # W, H = size
        print(bgColor)
        image = Image.new("RGBA", (W, H), bgColor)
        draw = ImageDraw.Draw(image)
        _, _, w, h = draw.textbbox((0, 0), message, font=font)
        draw.text(((W - w) / 2, (H - h) / 2), message, font=font, fill=fontColor)
        # (e, n, w, s)
        image = ImageOps.expand(image, border=(0, padding, 0, padding), fill=bgColor)
        return image

    @staticmethod
    def concatenate_images_v(img1, img2, img3=None):
        """
        Concatenates two images vertically
        """
        dst = Image.new(
            "RGBA", (max(img1.width, img2.width), img1.height + img2.height)
        )
        dst.paste(img1, (0, 0))
        dst.paste(img2, (0, img1.height))

        if img3:
            logging.debug("concatenating 3 images")
            rtnImg = Image.new(
                "RGBA", (max(dst.width, img3.width), dst.height + img3.height)
            )
            rtnImg.paste(dst, (0, 0))
            rtnImg.paste(img3, (0, dst.height))
            return rtnImg
        else:
            logging.debug("concatenating 2 images")
            return dst

    @staticmethod
    def calc_text_size(font_px: int, px_mult: int, dpi: int = settings.DPI) -> int:
        """
        Calculates the text size in inches based off of the font size in pixels
        """
        return int((font_px / px_mult) * dpi)

    @staticmethod
    def add_padding(img, padding, background_color):
        """
        Adds padding to the image
        """
        # add half the padding to the left and half to the right
        # (e, n, w, s)
        border = (int(padding / 2), 0, int(padding / 2), 0)
        return ImageOps.expand(img, border=border, fill=background_color)

    @staticmethod
    def add_text(
        img_path: str,
        out_path: str,
        text: dict,
        frame_size: str,
        verbose: bool = False,
        context: dict = None,
    ):
        # TO DO: change this function to take in multiple messages and error check
        # Constants for positioning based off of how many messages in dict.
        # img_path: path to image to add text to
        # out_path: path to save image with text
        # frame_size: _24_36
        """
        img_path: "path/to/image.png"
        out_path: "path/to/output.png"
        frame_size: _24_36
        text = {
            "primary": "LargeText",
            "secondary": "MediumText",
            "coordinate": "DelimitedDegreeMinutesSecondsWDirection",
        }
        context["textStylingSpecs"] ={
            'id': 'dark-transit',
            'iconImg': '/blackWhiteSquareIcon.svg',
            'url': 'https://api.maptiler.com/maps/265e1571-5b2a-47cf-bdf4-0f78abaefb47/{z}/{x}/{y}.png?key=fLxXsh3K0MP3y21i3bJs',
            'text': {
                'fontFamily': {
                    'primary': 'Semplicita',
                    'secondary': 'Semplicita',
                    'coordinate': 'Semplicita'
                },
                'size': {
                    'primary': '24',
                    'secondary': '12',
                    'coordinate': '8'
                },
                'color': {
                    'background': '#FFFFFF',
                    'primary': '#000000',
                    'secondary': '#000000',
                    'coordinate': '#000000'
                },
                'color_transparent': {
                    'background': '#0000',
                    'primary': '#FFFFFF',
                    'secondary': '#FFFFFF',
                    'coordinate': '#FFFFFF'
                },
                'textBlock': {
                    'padding': '8px', // Padding around text block (px)
                    'rounded': '8px', // Corners rounded (px)
                    'spacing': '1' // Inches between the bottom of the map and the bottom of the text block
                }
            }
        }
        """

        # Total size of image block
        map_img = Image.open(img_path)

        # Get text block background color, text color
        colorDict = context["textStylingSpecs"]["text"]["color"]
        if context["isTransparentTextBlock"]:
            colorDict = context["textStylingSpecs"]["text"]["color_transparent"]
        sizeDict = context["textStylingSpecs"]["text"]["size"]
        fontDict = context["textStylingSpecs"]["text"]["fontFamily"]
        textBlockSpecs = context["textStylingSpecs"]["text"]["textBlock"]

        # Generate the primary, secondary, coordinate text blocks
        primary_img = None
        secondary_img = None
        coordinate_img = None

        primary_img_width = 0
        secondary_img_width = 0
        coordinate_img_width = 0

        # style_dict = context["stylingSpecs"]
        # Put all text on transparent background
        transparent_background = (255, 0, 0, 0)
        if text["primary"] and text["primary"] != "":
            logging.debug(f'primary text found: {text["primary"]}')

            prim_font_size = Assembler.calc_text_size(
                font_px=int(sizeDict["primary"]),
                px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
                dpi=settings.DPI,
            )
            primary_font = ImageFont.truetype(
                map_font_path[fontDict["primary"]],
                prim_font_size,
            )

            # for concatenation
            primary_img_width = primary_font.getsize(text["primary"])[0]
            print(int(sizeDict["primary"]))
            # For padding on text images
            primary_img = Assembler.create_image(
                transparent_background,
                text["primary"],
                primary_font,
                colorDict["primary"],
                padding=Assembler.calc_text_size(
                    font_px=int(int(sizeDict["primary"]) / 4),
                    px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
                    dpi=settings.DPI,
                ),
            )
            if verbose:
                logging.info(
                    f"saving primary text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
                )
                primary_img.save(settings.TEMP_TEXT_OUTPUT_FOLDER + "primary-text.png")

        if text["secondary"] and text["secondary"] != "":
            logging.debug(f'secondary text found: {text["secondary"]}')
            sec_font_size = Assembler.calc_text_size(
                font_px=int(sizeDict["secondary"]),
                px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
                dpi=settings.DPI,
            )
            secondary_font = ImageFont.truetype(
                map_font_path[fontDict["secondary"]],
                sec_font_size,
            )

            # for concatenation
            secondary_img_width = secondary_font.getsize(text["secondary"])[0]

            secondary_img = Assembler.create_image(
                transparent_background,
                text["secondary"],
                secondary_font,
                colorDict["secondary"],
                padding=Assembler.calc_text_size(
                    font_px=int(int(sizeDict["secondary"]) / 4),
                    px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
                    dpi=settings.DPI,
                ),
            )
            if verbose:
                logging.info(
                    f"saving secondary text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
                )
                secondary_img.save(
                    settings.TEMP_TEXT_OUTPUT_FOLDER + "secondary-text.png"
                )

        if text["coordinate"] and text["coordinate"] != "":
            logging.debug(f'coordinate text found: {text["coordinate"]}')
            coord_font_size = Assembler.calc_text_size(
                font_px=int(sizeDict["coordinate"]),
                px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
                dpi=settings.DPI,
            )
            coordinate_font = ImageFont.truetype(
                map_font_path[fontDict["coordinate"]],
                coord_font_size,
            )
            # for concatenation
            coordinate_img_width = coordinate_font.getsize(text["coordinate"])[0]

            coordinate_img = Assembler.create_image(
                transparent_background,
                text["coordinate"],
                coordinate_font,
                colorDict["coordinate"],
                padding=Assembler.calc_text_size(
                    font_px=int(int(sizeDict["coordinate"]) / 4),
                    px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
                    dpi=settings.DPI,
                ),
            )
            if verbose:
                logging.info(
                    f"saving coordinate text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
                )
                coordinate_img.save(
                    settings.TEMP_TEXT_OUTPUT_FOLDER + "coordinate-text.png"
                )

        if primary_img is None and secondary_img is None and coordinate_img is None:
            logging.debug(
                "all text blocks are None, no text to add. Something might be wrong."
            )
            return

        # Before concatenation. Make sure that the text blocks are the same size.
        # If not, make them the same size. by adding padding of text block background color
        maxWidth = max(primary_img_width, secondary_img_width, coordinate_img_width)
        if primary_img and primary_img_width < maxWidth:
            primary_img = Assembler.add_padding(
                primary_img, maxWidth - primary_img_width, transparent_background
            )
            if verbose:
                logging.info(
                    f"saving primary text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
                )
                primary_img.save(
                    settings.TEMP_TEXT_OUTPUT_FOLDER + "primary-text-with-padding.png"
                )

        if secondary_img and secondary_img_width < maxWidth:
            secondary_img = Assembler.add_padding(
                secondary_img, maxWidth - secondary_img_width, transparent_background
            )
            if verbose:
                logging.info(
                    f"saving secondary text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
                )
                secondary_img.save(
                    settings.TEMP_TEXT_OUTPUT_FOLDER + "secondary-text-with-padding.png"
                )

        if coordinate_img and coordinate_img_width < maxWidth:
            coordinate_img = Assembler.add_padding(
                coordinate_img, maxWidth - coordinate_img_width, transparent_background
            )
            if verbose:
                logging.info(
                    f"saving coordinate text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
                )
                coordinate_img.save(
                    settings.TEMP_TEXT_OUTPUT_FOLDER
                    + "coordinate-text-with-padding.png"
                )

        # Now Concatenate the text blocks of the same width
        final_img = None
        if primary_img is None:
            if secondary_img is None:
                final_img = coordinate_img
            else:
                if coordinate_img is None:
                    final_img = secondary_img
                else:
                    # Append secondary and coordinate
                    final_img = Assembler.concatenate_images_v(
                        secondary_img, coordinate_img
                    )
        else:
            if secondary_img is None:
                if coordinate_img is None:
                    final_img = primary_img
                else:
                    # Append primary and coordinate
                    final_img = Assembler.concatenate_images_v(
                        primary_img, coordinate_img
                    )
            else:
                # Append primary and secondary
                final_img = Assembler.concatenate_images_v(primary_img, secondary_img)
                if coordinate_img:
                    # Append primary and secondary and coordinate
                    final_img = Assembler.concatenate_images_v(
                        final_img, coordinate_img
                    )

        if verbose:
            logging.info(
                f"saving final text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
            )
            final_img.save(settings.TEMP_TEXT_OUTPUT_FOLDER + "all-text.png")

        # Adding padding to text block
        padding = Assembler.calc_text_size(
            font_px=int(re.sub("[^0-9]", "", textBlockSpecs["padding"])),
            px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
            dpi=settings.DPI,
        )

        final_img = ImageOps.expand(
            final_img,
            border=(padding, padding, padding, padding),
            fill=transparent_background,
        )
        if verbose:
            logging.info(
                f"saving final text block with padding to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
            )
            final_img.save(
                settings.TEMP_TEXT_OUTPUT_FOLDER + "all-text-with-padding.png"
            )

        # Add rounded corner. Draw rectangle with rounded corners and paste the text image on top of it.
        radius = int(re.sub("[^0-9]", "", textBlockSpecs["rounded"]))
        if radius > 0:
            # radius = radius * context["mapDimensionsIn"]["map_pixel_multiplier"]
            radius = Assembler.calc_text_size(
                font_px=radius,
                px_mult=context["mapDimensionsIn"]["map_pixel_multiplier"],
                dpi=settings.DPI,
            )
            new_img_obj = Image.new("RGBA", final_img.size)
            draw = ImageDraw.Draw(new_img_obj)
            draw.rounded_rectangle(
                (0, 0, final_img.size[0], final_img.size[1]),
                radius,
                fill=colorDict["background"],
            )

            # Paste the text image on top of the rounded rectangle
            new_img_obj.paste(final_img, (0, 0), final_img)
            if verbose:
                logging.info(
                    f"saving final text block with padding and rounded corners to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
                )
                new_img_obj.save(
                    settings.TEMP_TEXT_OUTPUT_FOLDER
                    + "all-text-with-padding-rounded.png"
                )
            final_img = new_img_obj

        # Paste the image on the map.
        w, h = final_img.size
        map_width, map_height = map_img.size
        # text_block_y in inches
        text_block_y = float(textBlockSpecs["spacing"]) * settings.DPI
        paste_y = map_height - int(text_block_y + h)
        paste_x = (map_width / 2) - (w / 2)

        map_img.paste(final_img, (int(paste_x), int(paste_y)), final_img)
        if verbose:
            logging.info(
                f"saving final map with text block to {settings.TEMP_TEXT_OUTPUT_FOLDER}"
            )
            map_img.save(settings.TEMP_TEXT_OUTPUT_FOLDER + "map-with-text.png")

        map_img.save(out_path)
