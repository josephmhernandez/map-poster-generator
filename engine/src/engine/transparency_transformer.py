from PIL import Image, ImageOps
import logging

from src.constants.bg_images import BG_FOLDER_PATH, BG_IMG_URL_MAP

# Settings for TransparencyTransformer
BG_LOCATION_DEFAULT = "local"
BG_RATIO_DEFAULT = "2_3"


class TransparencyTransformer:
    @staticmethod
    def add_background_and_transparency(
        input_path: str,
        bg_img_code: str,
        output_path: str,
        bg_img_ratio: str = BG_RATIO_DEFAULT,
        bg_location: str = BG_LOCATION_DEFAULT,
    ):

        # Add alpha tile layer to bg image.
        # load the tile layer image.
        tile_img = Image.open(input_path)

        # load the bg image.
        logging.info("Looking for bg img: " + bg_img_code + " " + bg_img_ratio)
        bg_img_path = (
            BG_FOLDER_PATH[bg_location]
            + BG_IMG_URL_MAP[bg_img_code][bg_img_ratio][bg_location]
        )

        logging.info("Loading bg img: " + bg_img_path)
        bg_img = Image.open(bg_img_path)

        # Prepare Alpha layer image
        logging.info("Preparing alpha layer grayscale image")
        grayscale_img = tile_img.convert("L")
        inverted_grayscale_img = ImageOps.invert(grayscale_img)
        tile_img.putalpha(inverted_grayscale_img)

        # Paste alpha layer on top of bg image.
        logging.info("Adding alpha layer to bg image")
        # Check the direction of the tile image. If it's a vertical image, we need to rotate it.
        if tile_img.size[0] < tile_img.size[1]:
            logging.info("Rotating tile image")
            bg_img = bg_img.rotate(270, expand=True)
        # Ensure that tile image is the same size as bg image.
        if tile_img.size != bg_img.size:
            logging.error("WTF - the image sizes aren't the same")
            logging.error(
                "tile_img size -  "
                + str(tile_img.size)
                + " bg_img.size - "
                + str(bg_img.size)
            )
            raise Exception(
                "[TransparencyTransformer: add_background_and_transparency] WTF - the image sizes aren't the same"
            )

        bg_img.paste(tile_img, (0, 0), tile_img)

        logging.info("Saving bg image with alpha layer: " + output_path)
        bg_img.save(output_path)

    @staticmethod
    def add_white_background(input_path: str, output_path: str):
        # When we are playing with transparency in images and creating an alpha layer it's important to have a white background. This is because the alpha layer is a grayscale image and the white background will be the most transparent. If we don't have a white background, the alpha layer will be transparent in some places and opaque in others. This will cause the image to look weird when we add it to the background image.
        # Right now, planning to add tis to the end of the engine
        logging.info(
            "[TransparencyTransformer: add_white_background] Adding white background to image: "
            + input_path
        )

        img = Image.open(input_path)

        # If img isn't RGBA, convert it to RGBA
        if img.mode != "RGBA":
            logging.info(
                "[TransparencyTransformer: add_white_background] Converting image to RGBA"
            )
            img = img.convert("RGBA")

        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, (0, 0), img)

        logging.info(
            "[TransparencyTransformer: add_white_background] Saving image with white background: "
            + output_path
        )
        bg.save(output_path)
