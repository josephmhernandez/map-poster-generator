from enum import Enum
import logging

class Icon(Enum):
    CIRCLE = 1
    HEART = 2
    DIAMOND = 3

    # def __init__(self, name: str):

    #     if(name.upper() == "HEART"):
    #         return Icon.HEART
    #     elif(name.upper() == "CIRCLE"):
    #         return Icon.CIRCLE
    #     elif(name.upper() == "DIAMOND"):
    #         return Icon.DIAMOND


    #     raise ValueError("\"" + name + "\"" + " is not an Icon")