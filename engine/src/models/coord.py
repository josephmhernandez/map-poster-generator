from pickletools import long1
import decimal
import numpy as np
import mercantile


class Coord:
    def __init__(self, lon: decimal, lat: decimal):
        self.lon = decimal.Decimal(lon)
        self.lat = decimal.Decimal(lat)

    def __sub__(self, other):
        diff_log = decimal.Decimal(abs(self.lon - other.lon))
        diff_lat = decimal.Decimal(abs(self.lat - other.lat))

        return np.array([diff_log, diff_lat])

    def __str__(self):
        return "lon: " + str(self.lon) + ", lat: " + str(self.lat)

    def get_web_mercator(self) -> tuple:
        return mercantile.xy(lng=self.lon, lat=self.lat)

    def get_web_mercator_x(self) -> float:
        return mercantile.xy(lng=self.lon, lat=self.lat)[0]

    def get_web_mercator_y(self) -> float:
        return mercantile.xy(lng=self.lon, lat=self.lat)[1]
