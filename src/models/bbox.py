from unicodedata import decimal
from src.models.coord import Coord
import decimal
import numpy
import mercantile
import logging


class Bbox:
    def __init__(self, top_left: Coord, bottom_right: Coord):
        self.top_left = top_left
        self.bottom_right = bottom_right

    def __sub__(self, other):
        tl_lon = decimal.Decimal(self.top_left.lon - other.top_left.lon)
        tl_lat = decimal.Decimal(self.top_left.lat - other.top_left.lat)
        br_lon = decimal.Decimal(self.bottom_right.lon - other.bottom_right.lon)
        br_lat = decimal.Decimal(self.bottom_right.lat - other.bottom_right.lat)

        # return Bbox(Coord(tl_lon, tl_lat), Coord(br_lon, br_lat))
        return numpy.array([tl_lon, tl_lat, br_lon, br_lat])

    def lat_lon_print(self):
        print(
            ""
            + str(self.top_left.lat)
            + ","
            + str(self.top_left.lon)
            + ","
            + str(self.bottom_right.lat)
            + ","
            + str(self.bottom_right.lon)
            + ""
        )

    def __repr__(self):
        return (
            "[(lon: "
            + str(self.top_left.lon)
            + ", lat: "
            + str(self.top_left.lat)
            + "), (lon: "
            + str(self.bottom_right.lon)
            + ", lat: "
            + str(self.bottom_right.lat)
            + ")]"
        )

    def __str__(self):
        return (
            "[(lon: "
            + str(self.top_left.lon)
            + ", lat: "
            + str(self.top_left.lat)
            + "), (lon: "
            + str(self.bottom_right.lon)
            + ", lat: "
            + str(self.bottom_right.lat)
            + ")]"
        )

    def contains(self, coord: Coord) -> bool:
        # Checks if a point is contained in the bbox
        between_lon = False
        between_lat = False

        if coord.lon < max(
            self.top_left.lon, self.bottom_right.lon
        ) and coord.lon > min(self.top_left.lon, self.bottom_right.lon):
            between_lon = True

        if coord.lat < max(
            self.top_left.lat, self.bottom_right.lat
        ) and coord.lat > min(self.top_left.lat, self.bottom_right.lat):
            between_lat = True

        return between_lat and between_lon

    def get_dimensions_web_meractor(self) -> tuple:
        # Project longitude coordinate to web mercator and calculate the distance
        tl_x, tl_y = mercantile.xy(self.top_left.lon, self.top_left.lat)
        br_x, br_y = mercantile.xy(self.bottom_right.lon, self.bottom_right.lat)

        total_x_degree = abs(tl_x - br_x)
        total_y_degree = abs(tl_y - br_y)

        logging.info("total_x_degree: " + str(total_x_degree))
        logging.info("total_y_degree: " + str(total_y_degree))
        logging.info("the ratio of these should be the same as the poster length...")
        if total_x_degree < total_y_degree:
            logging.info("ratio: " + str(total_x_degree / total_y_degree))
        else:
            logging.info("ratio: " + str(total_y_degree / total_x_degree))

        return total_x_degree, total_y_degree
