# Note: Test Classes must start with "Test"
# Note: Test Functions must start with "test"

import settings
import os
import src.engine.engine_utils as engine_utils


class TestEngineUtils:
    def test_clean_folder(self):
        # assert that folder is created and that it is empty

        engine_utils.create_empty_folder(settings.TEMP_TILE_IMAGE_FOLDER)

        assert os.path.exists(settings.TEMP_TILE_IMAGE_FOLDER)
        assert len(os.listdir(settings.TEMP_TILE_IMAGE_FOLDER)) == 0
