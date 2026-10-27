import pytest

# Note: Test Classes must start with "Test"
# Note: Test Functions must start with "test"

from src.engine.downloader import Downloader
import settings
import os


class TestDowloader:
    def test_simple(self):
        assert 2 + 2 != 1
