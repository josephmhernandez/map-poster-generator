import logging
import pytest
from PIL import Image
import os
import glob
from src.engine.assembler import Assembler

# from src.models.print_format import PrintFormat
# from src.engine.validator import validate_json_attributes
import settings

# Note: Test Classes must start with "Test"
# Note: Test Functions must start with "test"


class TestAssembler:
    # Does not work
    # @pytest.fixture()
    # def setup_takedown(self):
    #     # Setup
    #     print("yo")
    #     yield
    #     # Tear Down

    #     # Remove all files from test_tile_images folder
    #     # TO DO: Remove all files from test/test_tile_images folder

    #     # Remove all files from /temp_output folder
    #     print("temp_output delete")
    #     files = glob.glob(f"{settings.TEMP_OUTPUT_FOLDER}*.png")
    #     for f in files:
    #         os.remove(f)
    #     pass

    def test_simple(self):
        print("running test_simple")
        assert 2 + 2 != 1

    # def test_add_text_all_blocks(self):
    #     logging.info("running test add_text")
    #     assembled_cropped_image = "test/assembler_unit_test_attachments/cropped_dc.png"
    #     map_img = Image.open(assembled_cropped_image)
    #     logging.info(f"size of the image: {map_img.size}")

    #     img_path = assembled_cropped_image
    #     out_path = "test.png"
    #     text_dict = {
    #         "primary": "Washington, DC",
    #         "secondary": "United States",
    #         "coordinate": "38.9072° N, 77.0369° W",
    #     }
    #     frame_size = "_24_36"
    #     style = "basic"
    #     context = {}
    #     context["stylingSpecs"] = {
    #         "block_inches": 4.5,
    #         "primary_font_size": 32,
    #         "primary_font": "Semplicita",
    #         "primary_font_color": "#000000",
    #         "secondary_font_size": 16,
    #         "secondary_font": "Semplicita",
    #         "secondary_font_color": "#000000",
    #         "coordinate_font_size": 12,
    #         "coordinate_font": "Semplicita",
    #         "coordinate_font_color": "#000000",
    #         "borders": [{"border_inches": 0.5, "color": "#FFFFFF"}],
    #     }
    #     context["mapDimensionsIn"] = {
    #         "map_width": 35,
    #         "map_height": 19,
    #         "map_pixel_multiplier": 23,
    #     }
    #     Assembler.add_text(
    #         img_path=img_path,
    #         out_path=out_path,
    #         text=text_dict,
    #         frame_size=frame_size,
    #         verbose=True,
    #         context=context,
    #     )

    #     prim_img = Image.open(settings.TEMP_TEXT_OUTPUT_FOLDER + "primary-text.png")
    #     sec_img = Image.open(settings.TEMP_TEXT_OUTPUT_FOLDER + "secondary-text.png")
    #     coord_img = Image.open(settings.TEMP_TEXT_OUTPUT_FOLDER + "coordinate-text.png")
    #     pre_padding_img = Image.open(settings.TEMP_TEXT_OUTPUT_FOLDER + "all-text.png")
    #     all_text_w_padding = Image.open(
    #         settings.TEMP_TEXT_OUTPUT_FOLDER + "add-text-w-padding.png"
    #     )

    #     prim_size = prim_img.size
    #     sec_size = sec_img.size
    #     coord_size = coord_img.size
    #     pre_padding_size = pre_padding_img.size
    #     all_text_w_padding_size = all_text_w_padding.size
    #     logging.info(f"size of the primary image: {prim_size}")
    #     logging.info(f"size of the secondary image: {sec_size}")
    #     logging.info(f"size of the coordinate image: {coord_size}")
    #     logging.info(f"size of the final image: {pre_padding_size}")
    #     logging.info(f"size of the final image w padding: {all_text_w_padding_size}")

    #     # Assert that each image generated is the correct size
    #     assert 626 == prim_img.size[1]
    #     assert 313 == sec_img.size[1]
    #     assert 234 == coord_img.size[1]
    #     assert 1173 == pre_padding_img.size[1]
    #     assert 1350 == all_text_w_padding.size[1]

    #     # Clean up temp_output folder
    #     assert True
    #     pass
