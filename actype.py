from collections import namedtuple
import csv, numpy as mp
from statistics import mean

# define named tuple
ACType = namedtuple('ACType',['wtc','wingspan','length','height','obs'])
ACType.__doc__ = """

Tuple representing ircraft dimensions

wtc - Wake turbulence category
wingspan - the aircraft's wingspan
length - the aircraft's length
height - the aircraft's height"""

def import_actype(filename:str = '.\\ac_dimensions.csv', delim : str = ';') -> dict:
    """ 
    Reads a database of aircraft dimensions.

    Args:
        filename (str, optional): CSV file that contains the database.  Defaults to '.\ac_dimensions.csv'.
        delim : column delimiter of the CSV file. Defaults to ";"

    Returns:
        Dictionary where the keys are the strings containing the ICAO 4 char code for the aircraft type and the values are named tuples of type ACType
    """
    # initialize the dictionary
    aircraft_dict = {}
    
    # read from the file
    try:
        reader = csv.DictReader(open(filename), delimiter=';')
    except:
        # if there's any problem reading the file, returns an empty dictionary
        return aircraft_dict
   
    for line in reader:
        try:
            aircraft_dict[line["ACTYPE"]] = ACType(line['WAKE'],float(line['WS']),float(line['LEN']),float(line['HGT']),line['OBS'])
        except:
            pass
    
    # calculate mean values for heavy aircraft
    selected = list(filter(lambda a: a.wtc == 'H', aircraft_dict.values()))
    aircraft_dict['H'] = ACType('H', mean(list(map(lambda a:a.wingspan, selected))), mean(list(map(lambda a:a.length, selected))), mean(list(map(lambda a:a.height, selected))),'Mean dimensions for heavy aircraft')
    
    # calculate mean values for medium aircraft
    selected = list(filter(lambda a: a.wtc == 'M', aircraft_dict.values()))
    aircraft_dict['M'] = ACType('M', mean(list(map(lambda a:a.wingspan, selected))), mean(list(map(lambda a:a.length, selected))), mean(list(map(lambda a:a.height, selected))),'Mean dimensions for medium aircraft')
    
    # calculate mean values for light aircraft
    selected = list(filter(lambda a: a.wtc == 'L', aircraft_dict.values()))
    aircraft_dict['L'] = ACType('L', mean(list(map(lambda a:a.wingspan, selected))), mean(list(map(lambda a:a.length, selected))), mean(list(map(lambda a:a.height, selected))),'Mean dimensions for light aircraft')
    
    # calculate mean values for ALL aircraft
    selected = list(aircraft_dict.values())
    aircraft_dict['ALL'] = ACType('ALL', mean(list(map(lambda a:a.wingspan, selected))), mean(list(map(lambda a:a.length, selected))), mean(list(map(lambda a:a.height, selected))),'Mean dimensions for all aircraft')

    # return the dictionary
    return aircraft_dict

def get_actype(atype:str) -> ACType:
    """
    Get the dimensions for a specific aircraft type

    Args:
        atype (str): Aircraft type to lookup

    Returns:
        ACType: Named tuple with the request aircraft type's dimensions
    """
    return aircraft_types[atype] if atype in aircraft_types else aircraft_types['ALL']
    
aircraft_types = import_actype()