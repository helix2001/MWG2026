from module import *
from module import Vector3D
from  datetime import datetime as dt
from dateutil.parser import parse
from time import time
from geographiclib.geodesic import Geodesic
from math import floor, ceil 
import numpy as np
from math import pi, sin, cos, sqrt
from module.geo import mod

def seconds_from_midnight(timestamp: datetime) -> float:
    """Calculates the number of seconds from midnight for a given datetime object
    Args:
        seconds (datetime): datetime object to calculate the seconds from midnight
    """
    try:
        result = (dt.combine(MIDNIGHT, timestamp.time()) - MIDNIGHT).total_seconds()
    except:
        result = None
    return result


class Report:
    """
    Class that will represent a single position report.
    Can be real or interpolated.
    """
    
    def __init__(self, info: dict, interpolated: bool = False):
        """
        Creates a position report

        Args:
            info (dict): Dictionary with the report data
            interpolated (bool, optional): Flag that indicates if the report is interpolated or a real one. Defaults to False.
        """
        # get latitude from the dictionary
        # initially self.lat
        try:
            self.lat = float(info[LAT])
        except:
            self.lat = None
        
        # get longitude from the dictionary
        try:
            self.long = float(info[LONG])
        except:
            self.long = None

        # get flight level from the dictionary
        try:
            self.fl = float(info[FL])
        except:
            self.fl = None

        # string representing the timestamp
        self.timestamp = None
        
        # timestamp in datetime
        self.timestamp_bin = None
        
        # seconds from midnight
        self.seconds = None
        
        # get the timestamp as string and binary from the dictionary
        if info and TIMESTAMP in info:
            temp = info[TIMESTAMP]
            
            if isinstance(temp, datetime.datetime):
                self.timestamp_bin = temp            
            else:
                self.timestamp = info[TIMESTAMP]
                try:
                    self.timestamp_bin = parse(self.timestamp)
                except:
                    self.timestamp_bin = None

            # try to convert to seconds (UNIX epoch time)
            try:
                self.timestamp_unix = dt.timestamp(self.timestamp_bin)                    
            except:
                self.timestamp_unix = None

            try:
                self.seconds_from_midnigh = seconds_from_midnight(self.timestamp_bin)
            except:
                self.seconds_from_midnigh = None
                
        
        # reads the seconds from midnight if not already calculated
        if self.seconds is None and SECONDS in info:
            self.seconds = float(info[SECONDS])

        # reads the ground track received in the aircraft's report
        try:
            self.ground_track = float(info[GT])
        except:
            self.ground_track = None
        
        # reads the ground speed received in the aircraft's report
        try:
            self.ground_speed = float(info[GS])
        except:
            self.ground_speed = None

        # read the hex code from the aircrafts report
        self.addr = info[CODE] if info and CODE in info else None

        # read the cross track error from the aircrafts report
        self.cte = info[CTE] if info and CTE in info else None
        
        # sets the value of the flag INTERPOLATED
        self.interpolated = interpolated

        # reads the value of the latitude projected on the nominal route, if exists
        self.proj_lat = info[PROJ_LAT] if info and PROJ_LAT in info else None
        # reads the value of the longitude projected on the nominal route, if exists
        self.proj_lon = info[PROJ_LON] if info and PROJ_LON in info else None

        # reads the value of the SAC from the position report
        self.sac = info[SAC] if info and SAC in info else None
        # reads the value of the SIC from the position report
        self.sic = info[SIC] if info and SIC in info else None

    def interpolate_with(self, r):
        """ Calculates the interpolation with a 2nd report, at the exact second after the first report
        Assumes that the reports are very close.
        Args:
            r (Report): Report to perform the interpolation with

        Returns:
            Report: interpolated position report
        """
        
        # verifies if self is already at the required second
        # if so, the method returns the object itself
        # beware of floating point comparisons.
        if self.seconds == floor(self.seconds): 
            # create a new report
            result: Report = self
        
        # only continue if r exists
        elif r:
            # determine the timestamp, in seconds from midnight, you're aiming for
            seconds = ceil(self.seconds)
            # verifies if the 2nd report timestamp is at the required timestamp
            if r.seconds == seconds:
                # create a new report
                result = r
            else:
                # interpolate the point to create a new report
                # calculate the distance and bearing from point 1 to point 2
                # using GeographicLib
                calc1 = Geodesic.WGS84.Inverse(lat1=self.lat, lon1=self.long, lat2=r.lat, lon2=r.long)
                distance = calc1["s12"]
                azimuth = calc1["azi1"]

                # elapsed time between the two reports
                delta = abs(self.seconds - r.seconds)

                # elapsed time between the first report and the timestamp we are interpolating at
                delta2 = seconds - self.seconds
                
                # calculate speed, might not match the ADS-B report speed.
                # result in meters/second
                speed = distance / delta

                # calculate the distance traveled from the first report to the position at
                # the desired timestamp
                dist = distance * delta2 / delta

                # calculate the required fix, given the distance traveled and the initial
                # bearing obtained in calc1
                calc2 = Geodesic.WGS84.Direct(lat1=self.lat, lon1=self.long, s12=dist, azi1=azimuth)
                lat = calc2["lat2"]
                long = calc2["lon2"]
                azi = calc2["azi2"]

                # calculate the FL at the interpolation point
                fl =  self.fl+ (r.fl-self.fl) /delta * delta2 

                holder = {LAT: lat, LONG: long, FL: fl, SECONDS: seconds, GT: azi, GS: speed * 3600 / 1852}

                # create the report object to hold the result.
                result: Report = Report(holder, interpolated=True)

        else:
            result = None

        return result
                            
    def __str__(self) -> str:
        """Create an information string for this position report
        Returns:
            str: _description_
        """
        return f'{self.seconds}; {self.fl};{self.lat};{self.long};{self.gt};{self.gs};{self.addr}'

    @property
    def valid(self) -> bool:
        """Checks if a position report is valid.
        At least lat, long, fl and timestamp must exist
        Returns:
            bool: True if the report is valid, false otherwise
        """
        return True if self.lat is not None and self.long is not None and self.fl is not None and (self.timestamp is not None or self.seconds is not None) else False

    """
    @property
    def resumo(self) -> tuple:
        Getter for a resume of the position report
        Returns:
            tuple: returns the timestamp, lat, long, timestamp_bin
        
        return (self.timestamp, self.lat, self.long, self.timestamp_bin)
        """
    
    @property
    def projected(self) -> tuple[float,float]:
        """Returns a tuple with the projected coordinates on the cleared route

        Returns:
            tuple[float,float]: Projected coordinates on the route
        """
        return self.proj_lat, self.proj_lon


def get_timestamp_bin(r: Report) -> datetime:
    return r.timestamp_bin

"""
def get_seconds(r: Report) -> float:
    return r.seconds

def get_timestamp(r: Report) -> str:
    return r.timestamp

"""