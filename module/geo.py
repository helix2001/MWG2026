# Geodesic and Haversine calculations for geographic coordinates
# Provides functions for direct and inverse geodesic calculations using the Haversine formulas.
# Implements geodesic calculations using spherical and mean Earth models.

# as per MWG FOX PROCESS Requirements v1.0, Paragraph 1.2
# Adds an error constant for latitude/longitude/distances/bearings calculations of up to 0.3%

# removed all refere
from math import radians, acos, asin, sin, cos, sqrt, pi, degrees, atan2, floor, trunc, pow, atan
import math
from string import digits
import sys
from turtle import distance
import numpy as np

# WGS84 semimajor axis 
A = 6378137.0

# WGS84 semiminor axis;
B = 6356752.3142

ERROR_CONSTANT = 0.003          # 0.3% error for latitude/longitude/distances/bearings calculations
EPS = sys.float_info.epsilon    # machine epsilon for floating point comparisons

# spherical Earth
SPHERICAL_RADIUS = 180 * 60 / pi * 1852

# WGS84 mean radius, calculated as the radius of a sphere with the same surface area as the ellipsoid
# returns more accurate results for geodesic calculations compared to the WGS84 ellipsoid model
MEAN_RADIUS = 6372008.8

# mean earth radius between 0º lat and 50º lat, returns less accurate results for higher latitudes
# this logic could be used to calculate a more accurate mean radius for specific latitude ranges

MEAN_RADIUS_0_50 = 6377890.41

# DEGTORAD = 2.0 * pi / 360.0
# RADTODEG = 1 / DEGTORAD

"""
convert distances from meters to nautical miles
"""
m2NM = 1852 # (should be 1/1852.0)

# error
ERROR_LATLONG = None

# N, E - positive values
# S, W - negative values

# floating point modulus
# see if this is implemented in some low level C/C++ library
def mod(y: float, x: float) -> float:
    return y - x * floor(y / x)

# calculates the smallest angle between to bearings
# used to determine if two flights are same or opposite direction
# already optimized

def heading_diff(h1:float, h2:float)->float:
    h1 = radians(h1)
    h2 = radians(h2)

    return round(degrees(acos(( cos (h1) * cos(h2) +sin(h1) * sin(h2)) )), 3)

# calculates the mean earth radius for a given latitude based on the WGS84 ellipsoid model

# TODO
# evaluate if this formula provides sufficient accuracy for all latitude ranges,
# especially near the poles where the curvature of the Earth changes more rapidly.
# and if its more accurate than using a single value for the mean earth radius across all latitudes.

def mean_radius_lat(lat: float) -> float:
    """
    returns the mean earth radius for a given latitude, which should be in degrees
    """
    try:
        lat = radians(abs(lat))
        result = sqrt(((A**2 * cos(lat))**2 + (B**2 * sin(lat))**2)/ ((A * cos(lat))**2 + (B * sin(lat))**2))
    
    except Exception as e:
        result = None

    return result

# given lat/lon, bearing and distance, determine the point lat/lon 
def direct_haversine(lat1:float, lon1:float, bearing:float, distance:float) -> tuple[float|None,float|None, float|None]:
    """
    calculates the destination lat,lon, given the initial lat, lon , ground track and distance (meters)
    returns the latitude and longitude of the destination point, or None, None if any error occured
    and the bearing at the destination point.
    """
    try:
        # calculate the destination point, considering the earth as a sphere
        lat1, lon1, bearing, distance = map(lambda a : radians(a),[lat1, -lon1, bearing, distance/1852/60])
        lat = asin(sin(lat1)*cos(distance)+cos(lat1)*sin(distance)*cos(bearing))
        dlon = atan2(sin(bearing)*sin(distance)*cos(lat1),cos(distance)-sin(lat1)*sin(lat))
        lon = mod(lon1-dlon +pi, 2*pi )-pi
        
        # calculate the reverse bearing, used to determine if a flight is crossing or reciprocal
        dlon = -lon1 + lon
        dlat = lat1 - lat
        # a = sin(dlat/2)**2 + cos(lat)*cos(lat1)*sin(dlon/2)**2
              
        final_bearing = mod(atan2(sin(dlon)*cos(lat1),cos(lat)*sin(lat1)-sin(lat)*cos(lat1)*cos(dlon)) + pi, 2 * pi)

        # calculate the results in degrees
        # if we implement the direct calculations, will it be faster ?
        lat, lon, final_bearing = map(lambda a : degrees(a),[lat,-lon,final_bearing])
        # final_bearing = round(mod (final_bearing, 360), 3)

    # for debugging purposes
    except Exception as e:
        print(e)
        lat = None
        lon = None
        final_bearing = None

    return lat, lon, final_bearing

def inverse_haversine(lat1:float, lon1:float, lat2:float, lon2:float) -> tuple[float|None,float|None, float|None]:
    """
    calculates the distance and bearing from P1 to P2, given the latitudes and longitudes of both points
    returns the distance in meters and the initial bearing in degrees, or None if any error occured
    """
    try:
        lat1, lon1, lat2, lon2 = map(lambda a : radians(a),[lat1, -lon1, lat2, -lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance = c * MEAN_RADIUS        
        bearing = mod(degrees(atan2(sin(-dlon)*cos(lat2),cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(-dlon))), 360)
        bearing_reverse = mod(degrees(atan2(sin(dlon)*cos(lat1),cos(lat2)*sin(lat1)-sin(lat2)*cos(lat1)*cos(dlon))), 360)

    # for debugging purposes
    except Exception as e:
        print(e)
        distance = None
        bearing = None
        bearing_reverse = None

    return distance, bearing, bearing_reverse

# calculates the initial bearing from P1 to P2, in radians
# if parameter convert is true, converts from degrees to radians

def bearing_haversine(lat1: float, lon1: float, lat2: float, lon2: float, convert: bool = True) -> float:
    # check if these special cases are needed, or if removing them will change the results
    # or speed of execution

    if lat1 == 90.0:
        # initial bearing from North Pole is always 180
        b = pi
    elif lat1 == -90.0:
        # initial bearing from South Pole is always 0
        b = 0.0
    else:
        # calculate initial bearing from p1 to p2, considering the earth as a sphere
        if convert:
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        b = mod(atan2(sin(lon2 - lon1) * cos(lat2), cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)),
                2 * pi)
    # returns initial bearing from (lat1,lon1) to (lat2,lon2), in degrees
    return degrees(b)

def distance_haversine(lat1: float, lon1: float, lat2: float, lon2: float, radius: float = MEAN_RADIUS) -> float:
    """
    Calculate the great-circle distance between two points using the Haversine formula.

    Args:
        lat1, lon1: Latitude/longitude of the first point in decimal degrees.
        lat2, lon2: Latitude/longitude of the second point in decimal degrees.
        radius: Sphere radius in meters (defaults to WGS84 mean Earth radius).

    Returns:
        Distance in meters.
    """

    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2.0) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2.0) ** 2
    c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a))
    return radius * c

def str_to_latlong(point: str) -> tuple[float, float]:
    # allowed format
    # DD[MM[SS]](N|S)DDD[MM[SS]](E|W)
    # lat, DD<=90, long DD<=180
    # MM <=59
    # SS <= 59
    result = (ERROR_LATLONG, ERROR_LATLONG)
    # positive latitudes, northern hemisphere
    latitude = 1
    # negatives longitudes, western hemisphere
    longitude = -1
    # make sure the letters are uppercase
    point = point.upper()
    # split string in latitude and longitude
    coords = point.split("N")
    if len(coords) < 2:
        # there is no N in the string
        # actually, the format might be wrong
        coords = point.split("S")
        if len(coords) == 2:
            # the point has a southern latitude
            latitude = -1
        else:
            # string incorrect, no indication of latitude
            return result

    lat_str = coords[0]
    long_str = coords[1][:-1]
    lc = coords[1][-1]

    if lc == "E":
        longitude = 1
    elif lc != "W":
        return result

    # check if  there's a correct number of characters in lat_str and long_str
    if not (len(lat_str) in [2, 4, 6]) or not (len(long_str) in [3, 5, 7]):
        return result

    for e in lat_str:
        # there's a non digit in the latitude
        if not (e in digits):
            return result

    for e in long_str:
        # there's a non digit in the longitude
        if not (e in digits):
            return result

    lat_deg = int(lat_str[:2])
    lat_minutes = lat_str[2:4]
    if lat_minutes != "":
        lat_min = int(lat_minutes)
        lat_seconds = lat_str[4:7]
        if lat_seconds != "":
            lat_sec = int(lat_seconds)
        else:
            lat_sec = 0
    else:
        lat_min = 0
        lat_sec = 0

    if lat_deg > 90 or lat_min > 59 or lat_sec > 59 or (lat_deg == 90 and (lat_min != 0 or lat_sec != 0)):
        return result

    latitude = (lat_deg + lat_min / 60 + lat_sec / 3600) * latitude

    lon_deg = int(long_str[:3])
    lon_minutes = long_str[3:5]
    if lon_minutes != "":
        lon_min = int(lon_minutes)
        lon_seconds = long_str[5:8]
        if lon_seconds != "":
            lon_sec = int(lon_seconds)
        else:
            lon_sec = 0
    else:
        lon_min = 0
        lon_sec = 0

    if lon_deg > 180 or lon_min > 59 or lon_sec > 59 or (lon_deg == 180 and (lon_min != 0 or lon_sec != 0)):
        return result

    longitude = (lon_deg + lon_min / 60 + lon_sec / 3600) * longitude

    return latitude, longitude


def degree_to_dms(n: float) -> tuple[int, int, int, int]:
    
    """
    Returns the representation of a float in deg, min, sec
        Args: number to convert
        Returns: degrees, minutes, seconds, sign of the value
    """
    sign = -1 if n<0.0 else 1    
    n = abs(n)
    d = trunc(n)
    n = (n - d) * 60
    m = trunc(n)
    n = (n - m) * 60
    s = round(n)
    if s == 60:
        s = 0
        m += 1
    if m > 59:
        m = 0
        d += 1
    return d, m, s, sign 

def degree_to_dms_dec(n: float) -> tuple[int, int, float, int]:
    """
    Returns the representation of a float in deg, min, decimal seconds
        Args: number to convert
        Returns: degrees, minutes, seconds, sign of the value
    """
    if n < 0.0:
        signal = -1
    else:
        signal = 1
    n = abs(n)
    d = trunc(n)
    n = (n - d) * 60
    m = trunc(n)
    s = (n - m) * 60
    # s = round(n)
    # if s == 60:
      #  s = 0
       # m += 1
    # if m > 59:
      #  m = 0
       #  d += 1
    return d, m, s, signal

# convert a pair lat, lon to a string, formatted as  "DDMMSS.CC(N|S)DDDMMSS.CC(W|E)"
def latlong_to_str_dec(lat: float, lon: float) -> str:
    # make sure the values are within limits
    if lat is None or lon is None or lat > 90.0 or lat < -90.0 or lon > 180.0 or lon < -180.0:
        return None

    chars = [["", "N", "S"], ["", "E", "W"]]

    lat_deg, lat_min, lat_sec, sign_lat = degree_to_dms_dec(lat)
    lon_deg, lon_min, lon_sec, sign_lon = degree_to_dms_dec(lon)

    lat_char = chars[0][sign_lat]
    lon_char = chars[1][sign_lon]

    return "{:0>2}{:0>2}{:05.2f}{}{:0>3}{:0>2}{:05.2f}{}".\
        format(lat_deg, lat_min, lat_sec, lat_char, lon_deg, lon_min, lon_sec, lon_char)

# check if a point is on a great circle
def point_on_gc(lat1:float,long1:float,lat2:float,long2:float, latx:float, longx:float) -> bool:
    result =  False
    # TODO check if the computations are faster without the special cases
    if long1 == long2 and long1 == longx:
        result = True
    elif  long1 == long2 and long1 != longx:
        result =False
    else:
        lat1, long1, lat2, long2, latx, longx = map(lambda a : radians(a),[lat1,long1,lat2,long2,latx,longx])
        newlat : float = atan((sin(lat1)*cos(lat2)*sin(longx-long2)-sin(lat2)*cos(lat1)*sin(longx-long1))\
            /(cos(lat1) * cos(lat2) * sin(long1 - long2)))

        # error is less than 30cm
        # print(round(degrees(abs(newlat-latx)),4)*1852) # for debug only
        # 0.0002 is an arbitrary value, corresponds to less than 37.5 cm
        result = round(degrees(abs(newlat-latx)),0) == 0
    
    return result

def x_track_haversine(lat_1 :float, long_1 : float ,lat_2 : float, long_2:float, lat_x : float,long_x :float, convert:bool = False) -> tuple[float,float, float, float]:
    """ 
    Calculates the perpendicular distance from px->(latx,longx) to the great circle
    defined by P1 -> (lat1,long1) to P2 -> (lat2, long2) and the projected fix on the GC
    
    Using a spherical earth model, Haversine. Introduces an approximation error of 0.3%.
    
    Taken from https://edwilliams.org,
    """
    # xdistance, lat_px, long_px, alongdistance
    result = None

    # if the points are the same or too close, calculate the distance from
    # P1 to PX, Check last result

    if (lat_1 == lat_x and long_1 == long_x):
        result = 0.0, lat_1, long_1, 0.0
    elif (lat_2 == lat_x and long_2 == long_x):
        result = 0.0, lat_2, long_2, 0.0
    else:   
        lat1, lon1, lat2, lon2, latx, lonx = map(lambda a : radians(a) ,[lat_1,long_1,lat_2,long_2,lat_x,long_x])
        d1x = 2*asin(sqrt((sin((lat1-latx)/2))**2 + cos(lat1)*cos(latx)*(sin((lon1-lonx)/2))**2))
    
        if abs(lat_1-lat_2)<= EPS and abs(long_1-long_2)<= EPS:
            result = d1x * MEAN_RADIUS, lat_1, long_1, 0.0
        else:
            b1x = atan2(sin(lonx - lon1) * cos(latx), cos(lat1) * sin(latx) - sin(lat1) * cos(latx) * cos(lonx - lon1))
        
            b12 = atan2(sin(lon2 - lon1) * cos(lat2), cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1))
            b21 = mod(atan2(sin(lon1 - lon2) * cos(lat1), cos(lat2) * sin(lat1) - sin(lat2) * cos(lat1) * cos(lon1 - lon2)),2*pi)

            # get cross track distance        
            xdist = asin(sin(d1x) * sin (b1x-b12))
            # get along track distance
            adist = asin(sqrt( (sin(d1x))**2 - (sin(xdist))**2 )/cos(xdist))

            # check if the cross track point is ahead or behind P1
            bearing = b12 if b1x >= 0.0 else mod(b12, 2*pi)       
            
            # calculate the destination point, considering the earth as a sphere
            lat = asin(sin(lat1)*cos(adist)+cos(lat1)*sin(adist)*cos(bearing))
            dlon = atan2(sin(bearing)*sin(adist)*cos(lat1),cos(adist)-sin(lat1)*sin(lat))
            lon = mod(-lon1-dlon + pi, 2*pi )-pi

            r = direct_haversine(lat1, lon1, bearing, adist)

            # distance positive, right of track, negative, left of track
            result = xdist * MEAN_RADIUS, degrees(lat), -degrees(lon), adist * MEAN_RADIUS
    
    return result

def is_fix_inside(lat:float, long:float, fix_list:list) -> bool:
    """ 
    Calculates if a fix is inside a polygon defined by fix_lst.
    The polygon must be defined clockwise and must not have concavities.
    Not the best solution but useful
    """
    
    # we need at least 3 fixes to define a polygon
    if fix_list == None or len(fix_list)<3:
        result = None
    else:
        result = True
        # add the first fix to the end of the list, if it is an open line
        # must use float safe comparison
        if fix_list[0] != fix_list[-1]:
            temp = fix_list + [fix_list[0]]
        else:
            temp = fix_list
        # iterate throught all segments
        for i in range(0,len(temp)-1):
            # calculates the distance from the fix to the segment
            r = x_track_haversine(lat_1 = temp[i][0], long_1 = temp[i][1], lat_2 = temp[i+1][0], long_2 = temp[i+1][1], lat_x=lat, long_x=long)
            # if the distance is negative, the fix is to the left of the segment,
            # putting it oustide of the polygon
            if r[0]<0.0 :
                result = False
                break

    # returns the result    
    return result

def get_bounding_box_haversine(p : list, lateral : int = 100, time_ahead : int = 15, dist : int = None, time_behind : int = 0) -> list:
    """
    Calculate the bounding box for an aircraft
    Args:
        p: Tuple containing the position information
        lateral: lateral separation to apply, in NM, default 100
        distance: longitudinal distance ahead to apply, in NM
        time_ahead: longitudinal time ahead to apply in minutes, default 15
        time_behind: longitudinal time behind to apply in minutes, default 0

    Returns:
        Tuple containing 4 points, representing the lb, lt, rt, rb points of the bounding box
    """

    # the list in p contains the following information:
    # 0 - latitude
    # 1 - longitude     
    # 2 - altitude
    # 3 - heading
    # 4 - speed in knots
    
    lat = p[0]
    long = p[1]
    initial_bearing = p[3]
    
    # convert speed from knots to meters per minute
    speed = p[4] / 60 * 1852 
    
    #calculate the lateral distance in meters
    distance_lateral = lateral * 1852

    if dist is None:
        # calculate distance ahead from time_ahead and speed
        distance_ahead = abs(time_ahead) * speed
        # calculate distance behind from time_behind and speed
        distance_behind = abs(time_behind) * speed
    else:
        distance_ahead = dist * 1852 # convert NM to meters
        distance_behind = dist * 1852 # convert NM to meters

    # calculate the point behind, if needed
    if distance_behind > 0.0:
        latb, longb, azib = direct_haversine(lat1=lat, lon1 = long, bearing = initial_bearing + 180, distance = distance_behind)
        azib += 180
    else:
        latb = lat
        longb = long
        azib = initial_bearing

    # calculate bottom left corner
    lat_bl, lon_bl, azi_bl = direct_haversine(lat1=latb, lon1 = longb, bearing = azib - 90, distance = distance_lateral)
        
    # calculate bottom right corner
    lat_br, lon_br, azi_br = direct_haversine(lat1=latb, lon1 = longb, bearing = azib + 90, distance = distance_lateral)

    # calculate point ahead
    lat_a, lon_a, azi_a = direct_haversine(lat1=lat, lon1 = long, bearing = initial_bearing, distance = distance_ahead)
    
    # calculate top left corner
    lat_tl, lon_tl, azi_tl = direct_haversine(lat1=lat_a, lon1 = lon_a, bearing = azi_a - 90, distance = distance_lateral)

    # calculate top right corner
    lat_tr, lon_tr, azi_tr = direct_haversine(lat1=lat_a, lon1 = lon_a, bearing = azi_a + 90, distance = distance_lateral)
    

    return [(lat_bl, lon_bl), (lat_tl, lon_tl), (lat_tr, lon_tr), (lat_br, lon_br)]

if __name__ == "__main__":
    # test the functions
    pass