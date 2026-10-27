from enum import Enum

from pyparsing import col

class Border_Id(Enum):
    Single_border = 1
    Double_border = 2


class BorderStyle(Enum):
    border_id : Border_Id
    color: str
    
class IterableBorder(type):
    def __iter__(cls):
        return iter(cls.__name__)

class Border(object):
    __metaclass__ = IterableBorder
    width : int
    color : str

    def __init__(self, width:int, color:str):
        self.width = width
        self.color = color
