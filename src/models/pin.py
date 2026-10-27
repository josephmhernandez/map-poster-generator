from dataclasses import dataclass

from src.models.icon import Icon
from src.models.coord import Coord


class IterableBorder(type):
    def __iter__(cls):
        return iter(cls.__name__)


@dataclass
class Pin:
    icon: str  # enum for pin icon type
    location: Coord  # leaflet digital location (lon, lat)
    digital_width: int  # leaflet digital pin size (pixels)
    digital_height: int  # leaflet digital pin size (pixels)
    color: str  # TO DO: color hex code

    __metaclass__ = IterableBorder

    def __iter__(cls):
        return iter(cls.__name__)

    def __init__(
        self,
        icon: str,
        location: list,
        digital_width: int,
        digital_height: int,
        color: str,
    ) -> None:

        self.icon = icon.lower()
        self.location = Coord(location[0], location[1])
        self.digital_height = digital_height
        self.digital_width = digital_width
        self.color = color

    def get_web_mercator(self) -> tuple:
        return self.location.get_web_mercator()
