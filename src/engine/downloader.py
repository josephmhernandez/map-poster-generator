from multiprocessing.pool import ThreadPool
import logging
import requests
import shutil
import mercantile
import math
from src.models.bbox import Bbox
from src.models.coord import Coord
import os
from settings import TEMP_TILE_IMAGE_FOLDER
import settings
import glob
import src.engine.engine_utils as engine_utils
from src.style_constants import API_DICT


class Downloader:

    # @staticmethod
    # def start_downloader(context):
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #     result = loop.run_until_complete(Downloader.generate_tile_lists(context))
    #     return result

    def download_tile(x, y, z, url, file_name):
        url = url.replace("{z}", str(z))
        url = url.replace("{x}", str(x))
        url = url.replace("{y}", str(y))

        # Call the URL to get the image back
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            logging.error(f"Could not download tile: {url}")

        # Next we will write the raw content to an image
        with open(file_name, "wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

    @staticmethod
    def generate_tile_lists(context):

        map_bbox = context["bbox"]
        base_url = API_DICT[context["tileLayer"]]["url"]
        zoom = context["zoom"]

        logging.info("url for downloading " + base_url)

        # Top Left and Bottom Right tile.
        tl_tiles = mercantile.tile(
            float(map_bbox.top_left.lon),
            float(map_bbox.top_left.lat),
            zoom,
        )
        br_tiles = mercantile.tile(
            float(map_bbox.bottom_right.lon),
            float(map_bbox.bottom_right.lat),
            zoom,
        )

        x_tile_range = [tl_tiles.x, br_tiles.x]
        y_tile_range = [tl_tiles.y, br_tiles.y]

        # Check if folder exists, if not create it
        engine_utils.create_empty_folder(TEMP_TILE_IMAGE_FOLDER)

        # Loop over the tile ranges
        # TO DO: how to optimize performance here with pool size
        pool_size = 10
        pool = ThreadPool(pool_size)
        count = 0
        for i, x in enumerate(range(x_tile_range[0], x_tile_range[1] + 1)):
            for j, y in enumerate(range(y_tile_range[0], y_tile_range[1] + 1)):
                file_name = TEMP_TILE_IMAGE_FOLDER + str(i) + "." + str(j) + ".png"
                pool.apply_async(
                    Downloader.download_tile,
                    (x, y, zoom, base_url, file_name),
                )
                # logging.info("downloaded tile...")
                count += 1

        # Close Multi processing
        pool.close()
        pool.join()

        # Check to see if there are enough images in the folder
        if len(os.listdir(TEMP_TILE_IMAGE_FOLDER)) != count:
            raise RuntimeError(
                f"inncorrect number of files downloaded to assemble the image file: {len(os.listdir(TEMP_TILE_IMAGE_FOLDER))} != {count}"
            )

        logging.info(
            f"Downloaded tile grid size: {str(abs(x_tile_range[0] - x_tile_range[1]) + 1)} , {str(abs(y_tile_range[0] - y_tile_range[1]) + 1)}"
        )
        return [
            abs(x_tile_range[0] - x_tile_range[1]) + 1,
            abs(y_tile_range[0] - y_tile_range[1]) + 1,
        ]
