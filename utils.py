import sys 
import re
from module import Vector3D
from module.geo import mod
from flight import Flight
from module import ALT_THRESHOLD_1000
import pickle

from math import sin, cos, pi, sqrt
import numpy as np

def try_float(a) -> float:
    """
    converts a number to float
    Args:
        a (_type_): Number to convert
    Returns:
        float: Number in float format, or None if the conversion failed
    """

    try:
        result = float(a)
    except:
        result = None
    return result

def try_int(a) -> float:
    """
    converts a number to integer
    Args:
        a (_type_): Number to convert
    Returns:
        float: Number in Integer format, or None if the conversion failed
    """

    try:
        result = int(a)
    except:
        result = None
    return result

# consider applying a more WGS84 oriented solution
def calc_relative_speed(gs1:float = 0.0, h1:float = 0.0, vs1:float = 0.0, gs2:float = 0.0,  h2:float = 0.0, vs2:float = 0.0) -> Vector3D:
    """
    Calculates the relative speed between 2 flights
    Args:
        gs1 (float): _description_. Defaults to 0.0.
        h1 (float): _description_. Defaults to 0.0.
        vs1 (float): _description_. Defaults to 0.0., expected as feet per min
        gs2 (float): _description_. Defaults to 0.0.
        h2 (float): _description_. Defaults to 0.0.
        vs2 (float): _description_. Defaults to 0.0. expected as feet per min
    Returns:
        Vector3D: Vector that describes the relative speed, Va/b = Va - Vb
    """

    # along v1 track vector
    h2 = mod(h2 - h1, 360)
    h1 = 0.0

    # convert NM/H -> NM/min
    # gs1 = gs1/60
    # gs2 = gs2/60
    # convert deg -> radians
    # not needed, h1 is already 0.0
    # h1 = h1/180*pi
    h2 = h2/180*pi
    # convert NM/H -> NM/min
    # vs1 = vs1 / 60
    # vs2 = vs2 / 60
    
    # overkill to use numpy, but will use it anyway
    r1_speed = np.array([(gs1)*cos(h1), (gs1)*sin(h1), vs1])
    r2_speed = np.array([(gs2)*cos(h2), (gs2)*sin(h2), vs2])
    rel_speed = np.subtract(r1_speed, r2_speed)
    return Vector3D(rel_speed[0], rel_speed[1], rel_speed[2])

def save_flights(flights:dict, flights_per_second:dict = None, filename:str = ""):
    """
    creates a pickle dump of the file
    Args:
        flights (dict): flights dictionary
        filename (str, optional): filename of the pickle file
    """
    if filename != "":
        with open(filename, 'wb') as file:
            pickle.dump(flights, file)
            if flights_per_second is not None:
                pickle.dump(flights_per_second, file)
        file.close()

def load_flights(filename:str = "") -> tuple[dict,dict]:
    """
    Reads the lists from a pickle file
    Args:
        filename (str, optional): filename of the pickle file
    """
    flights = None
    flights_second = None

    try:
        if filename != "":
            with open(filename, 'rb') as file:
                flights = pickle.load(file)
                try:
                    flights_second = pickle.load(file)
                except:
                    flights_second = None
                file.close()
    except Exception as error:
        print(error)
    
    return flights, flights_second

def get_command_parameters() -> tuple[str,str]:
    """
    Gets the command parameters from the command line

    Returns:
        tuple[str,str]: first two parameters
    """
    l = len(sys.argv)
    filename = sys.argv[1] if l > 1 else None
    output = sys.argv[2] if l > 2 else None
    return filename, output