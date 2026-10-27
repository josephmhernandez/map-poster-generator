from src.style_constants import map_font_path, map_pin_path, map_style

import os


class TestMapStyleConstants:
    def test_pin_paths(self):
        for pin in map_pin_path:
            assert os.path.exists(map_pin_path[pin])

    def test_font_paths(self):
        for font in map_font_path:
            assert os.path.exists(map_font_path[font])
