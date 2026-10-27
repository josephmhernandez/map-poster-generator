import pytest
from src.models.value_validator import ValueValidator


class TestValidator:
    def test_has_text_flag_text_in_all(self):
        inputPayload = {
            "textPrimary": "Washington D.C.",
            "textSecondary": "DC, USA",
            "textCoordinates": "N 38°55'19.29\" W 76°57'3.56\"",
        }

        assert ValueValidator.extract_valid_text_flag(inputPayload) == True

    def test_has_text_flag_text_in_primary(self):
        inputPayload = {
            "textPrimary": "Washington D.C.",
            "textSecondary": "",
            "textCoordinates": "",
        }

        assert ValueValidator.extract_valid_text_flag(inputPayload) == True

    def test_has_text_flag_text_in_secondary(self):
        inputPayload = {
            "textPrimary": "",
            "textSecondary": "DC, USA",
            "textCoordinates": "",
        }

        assert ValueValidator.extract_valid_text_flag(inputPayload) == True

    def test_has_text_flag_text_in_coordinates(self):
        inputPayload = {
            "textPrimary": "",
            "textSecondary": "",
            "textCoordinates": "N 38°55'19.29\" W 76°57'3.56\"",
        }

        assert ValueValidator.extract_valid_text_flag(inputPayload) == True

    def test_has_text_flag_text_in_none(self):
        inputPayload = {
            "textPrimary": "",
            "textSecondary": "",
            "textCoordinates": "",
        }

        assert ValueValidator.extract_valid_text_flag(inputPayload) == False
