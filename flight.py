from __future__ import annotations
  
from pandas import read_csv, DataFrame
from numpy import histogram, arange, ceil, sum, linspace, squeeze, array
# from scipy import stats as sps
from statsmodels.distributions.empirical_distribution import ECDF
from module import *
from report import Report, get_timestamp_bin
from typing import Tuple
from module.geo import *
from geographiclib.geodesic import Geodesic
from math import ceil
from datetime import datetime
import re
from actype import *
from statistics import mode

def get_direction(direction:float):
    bearing = mod(direction, 360)
    return EASTBOUND if 5.0 <= bearing < 175.0 else \
           WESTBOUND if 185.0 < bearing <= 355.0 else \
           NORTHBOUND if (355.0 < bearing or 5.0 > bearing) else \
           SOUTHBOUND

def get_sub_field(field18: str) -> dict:
    """
    Breaks field 18 subfields
    Args:
        field18 (str): string containing the entire field
    Returns:
        dict: Contains the field 18 information in pairs subfield:value
    """

    result = {}
    field18 = re.sub('/ +','/',re.sub('/+','/',re.sub(' +/','/',field18.strip(" /"))))
    if '/' in field18:
        # field18 = re.sub('/ +','/',re.sub('/+','/',re.sub(' +/','/', field18.strip().strip('/'))))
        # split field18 information
        s = re.split('/', " ".join(field18.split()))
        # get subfield names
        subfields = list(map(lambda a: a.split(" ")[-1], s[:-1]))
        # get subfield values
        values = list(map(lambda a: a.strip().split(" ")[0:-1], s[1:]))
        # values[-1] = [s[-1]]
        # len(values)>0 and len(values) == len(subfields):
        values[-1].append(s[-1].split(" ")[-1])
        # create the result, using list comprehension
        result =  {subfields[i]: values[i] for i in range(len(subfields))}
    
    return result


def get_sub_field_except(field18: str) -> dict:
    """
    Breaks field 18 subfields
    Args:
        field18 (str): string containing the entire field
    Returns:
        dict: Contains the field 18 information in pairs subfield:value
    """
    """
    result = {}
    if '/' in field18:
        # split field18 information
        s = re.split('/', field18)
        # get subfield names
        subfields = list(map(lambda a: a.split(" ")[-1], s[:-1]))
        # get subfield values
        values = list(map(lambda a: a.split(" ")[0:-1], s[1:]))
        # values[-1] = [s[-1]]
        if len(values)>0 and len(values) == len(subfields):
            values[-1].append(s[-1].split(" ")[-1])
            # create the result, using list comprehension
            result =  {subfields[i]: values[i] for i in range(len(subfields))} """
    
    try:
        # split field18 information
        s = re.split('/', field18)
        # get subfield names
        subfields = list(map(lambda a: a.split(" ")[-1], s[:-1]))
        # get subfield values
        values = list(map(lambda a: a.split(" ")[0:-1].strip(), s[1:]))
        # values[-1] = [s[-1]]
        values[-1].append(s[-1].split(" ")[-1])
        # create the result, using list comprehension
        result =  {subfields[i]: values[i] for i in range(len(subfields))}
    except:
        result = {}
    
    return result


class Flight:
    """ Class that represents a single flight """
    
    def __init__(self, info: dict = None):
        """
        Create a new instance of a flight

        Args:
            info:   dictionary, contains the relevant information.
            
            The names of the keys are defined in ./module/__init__.py
        """
        
        # flags this flight as selected for processing or not. Default is False
        selected = False

        # get flight id, serves as primary key
        # a flight shall always have an id
        self.id : int = info[ID] if ID in info.keys() else None

        # flight callsign
        try:
            self.callsign = info[CALLSIGN].strip()
        except:
            self.callsign = None
            # to debug missing callsign information
            input(f'{info} press any key!')

        # flight aerodrome of departure
        self.departure: str = info[DEPARTURE] if DEPARTURE in info else None

        # flight aerodrome of destination
        self.destination: str = info[DESTINATION] if DESTINATION in info else None

        # flight rules
        self.flight_rules: str = info[FLIGHTRULES] if FLIGHTRULES in info else None

        # RNP capabilities
        self.rnp4 = True if RNP4 in info and info[RNP4] == "1" else False
        self.rnp10 = True if RNP10 in info and info[RNP10] == "1" else False

        # MOPS
        self.mops =info[MOPS] if info[MOPS] else None
        
        # get AC type and/or WTC
        self.actype = None
        self.wtc = None
        
        if ACTYPE in info:
            # split the ACTYPE in ACTYPE/WTC
            try:
                temp = info[ACTYPE].split('/')
            except:
                temp = []
               
            # do we have an ACTYPE ?
            if len(temp) > 0:
                # get the aircraft type
                self.actype = temp[0]
                # do we have an WTC ?
                if len(temp) > 1:
                    # get the WTC
                    self.wtc = temp[1]

        # only reads the WTC from the dictionary if it is still empty
        if WTC in info and self.wtc is None:
            self.wtc = info[WTC]
            
        # get aircraft dimensions from the aircraft types dataset
        # is it a known aircraft type ?
        if self.actype and self.actype in aircraft_types:
            self.acdimensions = aircraft_types[self.actype]
        
        # else do we have a know WTC ?
        elif self.wtc and self.wtc in aircraft_types:
            self.acdimensions = aircraft_types[self.wtc]
        
        # we don't have a known ACTYPE or WTC, use the mean dimensions of all known aircraft
        # will probably introduce BIAS
        else:
            self.acdimensions = aircraft_types['ALL']
            
        if EQUIP10A in info:
            # true if declared HLA, false otherwise
            self.hla = "X" in info[EQUIP10A]
            # true if declared HLA, false otherwise
            self.rvsm = "W" in info[EQUIP10A]
            # true if declared GNSS, false otherwise
            self.gnss = "G" in info[EQUIP10A]

            """ Long range datalink capabilities """
            # true if declared CPDLC HF, false otherwise
            self.cpdlc_hf: bool = "J2" in info[EQUIP10A]
            # true if declared CPDLC INMARSAT, false otherwise
            self.cpdlc_inmarsat: bool = "J5" in info[EQUIP10A]
            # true if declared CPDLC IRIDIUM, false otherwise
            self.cpdlc_iridium: bool = "J7" in info[EQUIP10A]

            if PBCS in info:
                # true if declared PBCS, false otherwise
                self.pbcs: bool = info[PBCS] == '1'
            elif SURV in info:
                # true if declared PBCS, false otherwise
                self.pbcs: bool = "P2" in info[EQUIP10A] and "RSP180" in info[SURV]

        if EQUIP10B in info:
            # true if declared ADS-C, false otherwise
            self.adsc: bool = "D1" in info[EQUIP10B]
            # true if declared ADS-B, false otherwise
            self.adsb: bool = "B1" in info[EQUIP10B] or "B2" in info[EQUIP10B] or "L" in info[EQUIP10B] or "E" in info[EQUIP10B]

        # get ADS-B status
        if ADSB in info:
            self.adsb = info["ADSB"] == '1'

        # ModeS / ADS-B hex code
        try:
            self.code = info[CODE].strip().rjust(6, "0")
        except:
            self.code = None

        # SQUAWK code
        self.ssr: str|None = info[SSR] if SSR in info else None

        # is the flight in the OTS
        self.ots = info[OTS] if OTS in info else '0'

        # will contain the list of surveillance reports, sorted by time ASC
        self.surveillance = []

        # will contain the list of interpolated position reports, to the second
        self.interpolated = {}

        # will contain the list of flight profile fixes, sorted by timestamp asc
        self.profile = []

        # dictionary of report duplicates
        # será mesmo necessário ?

        self.duplicates = {}
        
        # counter of position reports, used to count 
        self.counter = 0

        # ???
        self.sametime = 0

        self.max_fl = None
        self.min_fl = None

        self.direction = None

    def set_selected(self, log : bool = False):
        """
        defines the state of each flight, according to the presence of interpolated position reports, and the maximum and minimum levels found in these reports.
        log: if true, will print the reason why a flight is discarded, if it is the case.
        returns the state of the flight (selected or not)
        """
        if len(self.interpolated) > 1 and self.maxlevel >= 288.00 and self.minlevel <= 412.00:
            self.selected = True
        else:
            self.selected = False
            if log:
                print(f'Flight with id {self.id} is discarded.')
                if len(self.profile) < 2:
                    print('\tCleared profile incomplete.')
                if len(self.surveillance) < 2:
                    print(f'\tFlown profile incomplete.')
                if len(self.interpolated) < 2:
                    print(f'\tInterpolated profile incomplete.')
                if self.maxlevel<288.0:
                    print(f'\tThe flight was always below RVSM.')
                if self.minlevel>412.0:
                    print(f'\tThe flight was always above RVSM.')
                    
        return self.selected
    
    @property
    def elapsed_time_surveillance(self) -> float:
        
        try:
            result = (self.surveillance[-1].timestamp_bin - self.surveillance[0].timestamp_bin).total_seconds()
        except:
            result = None
        
        return result

    def elapsed_time_profile(self) -> float:
        try:
            result = (self.profile[-1].timestamp_bin - self.profile[0].timestamp_bin).total_seconds()
        except:
            result = None
        return result

    def elapsed_time_profile(self) -> float:
        try:
            timestamps = self.interpolated.keys()
            result = (timestamps[-1]- timestamps[0])
        except:
            result = None
        return result
    
    """
    # calculate the total flight time, in seconds
    @property
    def flight_time(self) -> float:
        try:
            start = self.surveillance[0].timestamp_bin
            finish = self.surveillance[-1].timestamp_bin
            # s = datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
            # f = datetime.strptime(finish, "%Y-%m-%d %H:%M:%S.%f")
            result = (finish-start).total_seconds()        
        except Exception as error:
            print(self.id, ' ',self.callsign,' ', error)
            result = 0.0
        return result    
    """

    def set_flight_direction_interpolated(self):       
        try:
            self.direction = mode(list(map(lambda a: get_direction(a[3]),list(self.interpolated.values()))))
        except Exception as error:
            self.direction = None
            # log error
    
    def average_speed_interpolated(self):
        if self.interpolated is not None and len(self.interpolated)>0:
            result = np.array([self.interpolated[item][4] for item in self.interpolated], dtype= float).mean()
        else:
            result = None        
        return result

    def py0_with(self, other : Flight) -> float:
        
        # determine the py0 considering only this flight and other specified flight
        # considering only the interpolated position reports, and the CTEs calculated from the real position reports
        # as if these two flights were the only ones in the airspace, and they were flying at the same time,
        # with the same speed and direction as in the interpolated position reports
        
        result = 0.0

        # determine simultaneous presence in the airspace        
        i_seconds = list(self.interpolated.keys())
        j_seconds = list(other.interpolated.keys())

        # do the timestamps of the position reports overlap ?
        if (i_seconds[0] <= j_seconds[0] <= i_seconds[-1]) or (j_seconds[0] <= i_seconds[0] <= j_seconds[-1]):
            start = i_seconds[0] if j_seconds[0] <= i_seconds[0] <= j_seconds[-1] else j_seconds[0]
            finish = i_seconds[-1] if j_seconds[0] <= i_seconds[-1] <= j_seconds[-1] else j_seconds[-1]
        
        # determine directions for individual timestamps
        dirs = []
        same = 0
        opp  = 0
        
        # determinar se são voos no mesmo sentido ou oposto.
        # rever para tráfego cruzado

        for i in range(start, finish + 1):
            if heading_diff(self.interpolated[i][3], other.interpolated[i][3]) < 90.0:
                same+=1
            else:
                opp +=1
                
        try:
            # get the wider wingspan, in NM
            WINGSPAN = max(self.acdimensions.wingspan, other.acdimensions.wingspan)/1852
    
            # get the ctes of both flights, from the interpolated list
            ctes = self.ctes
            ctes.extend(other.ctes)
        
            # determine the empirical cumulative distribution function for the CTEs
            data = DataFrame(ctes).to_numpy()
            ecdf = ECDF(data.T[0])
        
            # get the number of bins to interpolate
            min_cte = min(data)[0]
            max_cte = max(data)[0]
            count = int((max_cte-min_cte) / 0.001)
            bins = linspace(min_cte,max_cte,count)
            bins = array(list(zip(bins,bins[1:])))
        
            if same > opp:
                result = sum(list(map(lambda x : (ecdf (x[1] + WINGSPAN) - ecdf(x[0] - WINGSPAN)) * (ecdf (x[1]) - ecdf (x[0])) , bins)))
            else:
                result = sum(list(map(lambda x : (ecdf (-1*x[1] + WINGSPAN) - ecdf(-1 * x[0] - WINGSPAN)) * (ecdf (x[1]) - ecdf (x[0])) , bins)))

        except Exception as error:            
            with open('errors.py.txt','a') as f:
                f.write(f'ERROR on PY0 calc:{self.id},{self.callsign} against {other.id},{other.callsign}  {error}\n')

        return result

    def sum_dimensions_with(self, flight:Flight) -> Vector3D:
        #####
        # this probably is buggy
        #####
        """
        Calculates the sum of the dimensions of this flight's aircraft type with another flight's aircraft type

        Args:
            flight (Flight): Flight to sum the dimensions with.

        Returns:
            Vector3D: sum of the aircraft dimensions
        """        
        return Vector3D(self.acdimensions.x + flight.acdimensions.x,\
                      self.acdimensions.y + flight.acdimensions.y,\
                      self.acdimensions.z + flight.acdimensions.z)
    
    """
    @property
    def elapsed_time(self) -> float:
        return self.interpolated[-1] - self.interpolated[0]
    """
    
    @property
    def max_dimension(self) -> float|None:
        """
        Getter for the maximum value of an aircraft type dimensions.
        Returns:
            float: returns the highest value between the wingspan and the length for this flight's aircraft type
        """
        return max(self.acdimensions) if self.acdimensions else None

    @property
    def min_dimension(self) -> float| None:
        """
        Getter for the minimum value of an aircraft type dimensions.
        Returns:
            float: returns the lowest value between the wingspan and the length for this flight's aircraft type
        """
        return min(self.acdimensions) if self.acdimensions else None
    
    @property
    def ctes(self):
        """
        gets the  calculated Cross Track Errors from the surveillance reports list.
        Needed to calculate Py0

        Returns:
            list[float]: List containing the CTEs for the real position position reports
        """
        return list(map(lambda r : r.cte, list(filter(lambda r : r.cte is not None and -0.5<=r.cte<=2.5, self.surveillance)))) if self.surveillance is not None else None
    
    def __str__(self):
        """ Returns a string describing the flight. """
        return "{}-{}, de {} para {}, CODE {}".format(self.id, self.callsign, self.departure, self.destination,
                                                 self.code)
    
    def get_description(self):
        try:
            if self.profile and len(self.profile)!= 0:
                entry : Report = self.profile[0]
                exit : Report = self.profile[-1]
                elapsed_profile = round((exit.timestamp_bin - entry.timestamp_bin).total_seconds()/3600,2)
            
            result = [self.id, self.callsign, round(self.elapsed_time_surveillance()/3600, 2), elapsed_profile, self.actype, self.wtc, self.pbcs, self.code,
                      self.ots, len(self.profile), len (self.surveillance), len(self.interpolated),self.min_fl, self.max_fl, entry.lat, entry.long, entry.timestamp_bin,
                      exit.lat, exit.long, exit.timestamp_bin, self.surveillance[0].timestamp_bin, self.surveillance[-1].timestamp_bin]
        except Exception as error:
            result = None
            # print(error)
        return result
        
        
    def get_separation_with(self, other: Flight, ts : int = None):
        """
        Determines separation minima between two flights

        Args:
            other (Flight): the 2nd flight
            ts (int, optional): Timestamp (in seconds from midnight) to consider. Needed to determine the relative direction of the flights. Defaults to None.

        Returns:
            dict : Dictionary containing the various separation minima, and the protected boxes for both flights
        """

        lateral = SEP_RNP4 if self.rnp4 and other.rnp4 else \
            SEP_RNP10 if (self.rnp10 or self.rnp4) and (other.rnp4 or other.rnp10) else SEP_HLA

        precision = SEP_PBCS if self.is_dlm and self.pbcs and other.is_dlm and other.pbcs else SEP_NONPBCS
        precision = SEP_SURV if precision == SEP_PBCS and self.adsb and other.adsb else precision

        if ts is not None and ts in self.interpolated and ts in other.interpolated:
            # get the reports for the specified time stamp
            p1 = self.interpolated[ts]
            p2 = other.interpolated[ts]
            
            # calculate the relative angle between both flights, and caracterize them according to
            # PANS-ATM/DOC 7030/NAT DOC 008 - Application of separation minima
            angle = heading_diff(p1[3], p2[3])
            traffic_type = SAMEDIR if angle < 90.0 else RECIPROCAL

            # get the appropriate lateral separation minimum
            latsep = LAT_SEP[precision][lateral]

            # override the lateral separation minimum to be the same as the handbook
            latsep = 60
            
            # get the appropriate longitudinal separation minimum
            # for the relative direction of these flights
            longsep_ahead = LONG_SEP[traffic_type][BEFORE][precision][lateral]
            longsep_behind = LONG_SEP[traffic_type][AFTER][precision][lateral]

            # convert time minima in distance, for each aircraft,
            # as they have different speeds
            longsep_ahead_f1 = abs(longsep_ahead) * p1[4] / 60 if longsep_ahead < 0 else longsep_ahead
            longsep_behind_f1 = abs(longsep_behind) * p1[4] / 60 if longsep_behind < 0 else longsep_behind

            longsep_ahead_f2 = abs(longsep_ahead) * p2[4] / 60 if longsep_ahead < 0 else longsep_ahead
            longsep_behind_f2 = abs(longsep_behind) * p2[4] / 60 if longsep_behind < 0 else longsep_behind

            if traffic_type == OPPOSITE:
                longsep_ahead_f1 = 2 * longsep_ahead_f1 if longsep_ahead < 0 else longsep_ahead
                longsep_behind_f1 = 2 * longsep_behind_f1 if longsep_behind < 0 else longsep_behind

                longsep_ahead_f2 = 2 * longsep_ahead_f2 if longsep_ahead < 0 else longsep_ahead
                longsep_behind_f2 = 2 * longsep_behind_f2 if longsep_behind < 0 else longsep_behind
            else:
                longsep_behind_f1 = 0
                longsep_behind_f2 = 0

            # fixed longitudinal separation, to comply with the handbook
            if traffic_type == OPPOSITE:
                longsep_ahead_f1 = 15 * p1[4] / 60
                longsep_behind_f1 = 15 * p1[4] / 60
                longsep_ahead_f2 = 15 * p2[4] / 60
                longsep_behind_f2 = 15 * p2[4] / 60
            else:
                longsep_ahead_f1 = 15 * p1[4] / 60
                longsep_behind_f1 = 15 * p1[4] / 60
                longsep_ahead_f2 = 15 * p2[4] / 60
                longsep_behind_f2 = 15 * p2[4] / 60

            # protected airspace for flight1
            box1 = get_bounding_box_haversine(p=p1, lateral=latsep + 1, dist=longsep_ahead_f1, behind=longsep_behind_f1)
            # protected airspace for flight2
            box2 = get_bounding_box_haversine(p=p2, lateral=latsep + 1, dist=longsep_ahead_f2, behind=longsep_behind_f2)

        else:
            angle = None
            traffic_type = None
            box1 = None
            box2 = None

        return lateral, precision, angle, traffic_type, box1, box2, latsep, (longsep_ahead_f1 + longsep_ahead_f2)/2

    
    """
    @property
    def actype(self):
    #   Getter for the aircraft type
    #
    #   Returns:
    #       _type_: ICAO string for this aircraft type
     
        return self.actype
    """
    
    """
    @property
    def wtc(self):
        ###
        ###Getter for the WTC

        ###Returns:
           ### _type_: Wake turbulence category of the aircraft
        ###
        return self.wtc """
    
    """
    @property
    def maxlevel(self) -> float:
       
       # Highest level found in the interpolated position reports

        # Returns:
          #  float : highest level found in the interpolated position reports list
        
        if not self.interpolated or len(self.interpolated) == 0:
            maxfl=-1
        else:
            maxfl = max(list(map(lambda a: self.interpolated[a][2],self.interpolated)))
        return maxfl """

    """
    @property
    def minlevel(self) -> int:
       
       # Lowest level found in the interpolated position reports
        #Returns:
         #   float : highest level found in the interpolated position reports list
    
        if not self.interpolated or len(self.interpolated) == 0:
            minfl = -1
        else:
            minfl = min(list(map(lambda a: self.interpolated[a][2],self.interpolated)))
        return minfl
    """

    def clear_duplicates(self):
        """
        Clears the position reports duplicates list. Used when loading the flight.
        """
        self.duplicates = {}

    # used there are too many surveillance reports
    def decimate_surveillance(self, step = 10):
        if self.surveillance and step > 1:
            self.surveillance = self.surveillance[0:-1:step]
    
    """
    @property
    def sametime(self):
        return self.adsb
    """

    def set_duplicate(self, d):
        """
        Add a duplicate to the position reports list
        Args:
            d (_type_): _description_
        """
        self.duplicates[d] = 1

    def add_duplicate(self, d):
        """
        Increase the number of duplicates of a specific position report
        Args:
            d (_type_): _description_
        """
        self.duplicates[d] += 1

    """@property
    def acid(self) -> str:
        
        Getter for the Flight's callsign
        Returns:
            str: _description_
        
        return self.callsign """

    def direction_at_timestamp(self, ts: None) -> str:
        """
        Classify the direction of flight according to the heading
        Args:
            ts - timestamp to look for
        Returns: one of the values [NORTHBOUND, SOUTHBOUND, EASTBOUND, WESTBOUND]
        """
        result = None
        if ts in self.interpolated:
            # to take into account negative angles or angles > 360
            azimuth = mod(self.interpolated[ts][3], 360)

            result = EASTBOUND if 5.0 <= azimuth < 175.0 else \
                WESTBOUND if 185.0 < azimuth <= 355.0 else \
                NORTHBOUND if (355.0 < azimuth or 5.0 > azimuth) else \
                SOUTHBOUND
        return result
 
    @property
    def is_dlm(self) -> bool:
        """
        Getter for the property dlm

        Returns:
            bool: True if the flight complies with the DLM, false otherwise
        """
        return self.adsc and (self.cpdlc_hf or self.cpdlc_iridium or self.cpdlc_inmarsatinmarsat)

    def add_surv_rep(self, r: Report):
        """ Appends a position report to the surveillance reports list."""
        self.surveillance.append(r)

    def sep_5min(self) -> bool:
        """
        Determines if this flight can be considered for  5 min longitudinal separation minima

        Returns:
            bool : True if RNP4 or RNP10, and is PBCS certified, and is CPDLC connected
                 : False otherwise
        """
        return (self.rnp10 or self.rnp4) and self.pbcs and self.is_dlm

    def sort_reports(self):
        """ Sorts the surveillance reports list, based on the timestamp. Clears duplicate reports """
        self.surveillance.sort(key = get_timestamp_bin)
        
        # remove consecutive reports with dif timestamps but the same lat/long
        i=0
        while i < len(self.surveillance)-1:
            p1 = self.surveillance[i]
            p2 = self.surveillance[i+1]
            if (p1.lat == p2.lat and p1.long == p2.long):
                # print(i," - ", p1,"\n",p2)
                self.surveillance.pop(i)
            else:
                i+=1

    def sort_profile(self):
        """ Sort the flight's cleared profile """
        self.profile.sort(key = get_timestamp_bin)

        # remove consecutive identical reports with dif timestamps but the same lat/long
        i=0
        while i < len(self.profile)-1:
            p1 = self.profile[i]
            p2 = self.profile[i+1]
            if (p1.lat == p2.lat and p1.long == p2.long):
                # print(i," - ", p1,"\n",p2)
                self.profile.pop(i)
            else:
                i+=1

    def set_min_max_fl(self):
        """ Sets the flight's maximum and minimum flight levels, based on the surveillance reports list. """
        if self.surveillance and len(self.surveillance) > 0:
            self.max_fl = max(list(map(lambda r : r.fl, self.surveillance)))
            self.min_fl = min(list(map(lambda r : r.fl, self.surveillance)))

    def interpolate_all(self) -> dict:
        """ 
        Calculates the interpolated positions at whole seconds, from the first to the last surveillance
        report.  Will interpolate multiple times between two consecutive reports, if needed.
        Args:
            self
        Returns:  
            The array of interpolated reports in the format list of
                [lat, long, fl, azimuth, speed * 3600 / 1852, lat_10min, lon_10min, climb_rate]
                
                lat_10min, lon_10min represent the flight's position 10 minutes from now, at the current speed and ground track
        """

        # will hold the result dictionary.
        # keys will be the interpolated timestamps, in whole seconds from midnight
        result: dict = {}
        
        bearing = 0.0

        # we need at least 2 surveillance reports, currently step 0
        
        # surv = self.surveillance[0:-1]
        length = len(self.surveillance)
        if length > 1:
            
            # TODO determine here the ground track of the first position report

            # get the first second of the report, in unix timestamp 
            current_second = ceil(datetime.timestamp(self.surveillance[0].timestamp_bin))
            
            for i in range(0, length-1):
                p1: Report = self.surveillance[i]
                p2: Report = self.surveillance[i + 1]

                # Calculate elapsed time between the two reports. Assumes they are sorted by timestamp, ascending
                delta = (datetime.timestamp(p2.timestamp_bin) - datetime.timestamp(p1.timestamp_bin))
                if delta > 0.0:
                    # calc distance and initial bearing between two reports
                    # noinspection PyUnresolvedReferences
                    try:
                        dp1p2, bp1p2, bp2p1 = inverse_haversine(lat1 = p1.lat, lon1 = p1.long, 
                                                                lat2 = p2.lat, lon2 = p2.long)
                    except:
                        # maybe print an error message ? 
                        # proceed to next pair of reports
                        continue
                        
                    """
                    TODO determine rate of turn, to determine if the bearing is changing
                    between the two reports, and if so, to determine the bearing at the desired timestamp,
                    instead of assuming a constant bearing between the two reports.
                    """
                    
                    # verify if the points are the same
                    # if the distance is zero, we will not be able to calculate the speed, 
                    # and the position at the desired timestamp will be the same as the first report,
                    # so we can skip the calculations                    
                    if dp1p2 == 0:
                        # no_dist +=1 
                        # print(self.callsign,' ',no_dist, delta)
                        pass
                    
                    # calculates speed using the reports, in m/s
                    # speed = distance_p1p2 / delta
                    speed = dp1p2 / delta

                    # check if the flight is moving too too fast, set a global parameter
                    # this code serves just to set a breakpoint, if needed
                    if speed >= 350:
                        pass
                        # print(self.acid, " - speed ",speed, " at seconds ",seconds)

                    # calculate the altitude variation rate
                    # deverá ter em conta os reportes ADS-C com altitudes diferentes, poderá 
                    # deturpar a velociade vertical média

                    climb_rate = (p2.fl - p1.fl) / delta
                    
                    first_second = datetime.timestamp(p1.timestamp_bin) 
                    last_second = datetime.timestamp(p2.timestamp_bin)

                    # beware of floating point comparisons
                    while current_second <= last_second:                        
                        if first_second == current_second:
                            lat = p1.lat
                            lon = p1.long
                            fl = p1.fl
                            bearing = bp1p2 #calc1["azi1"]
                            # result[seconds] = [p1.lat,p1.long, p1.fl, p1.gt, p1.gs]
                        elif current_second == last_second:
                            lat = p2.lat
                            lon = p2.long
                            fl = p2.fl
                            #azimuth = calc1["azi2"] # ground track at the end of the segment
                            bearing = mod(bp2p1+180, 360)
                            # result[seconds] = [p2.lat,p2.long, p2.fl, p2.gt, p2.gs]
                        else:
                            #azimuth = bp1p2 #calc1["azi1"]
                            # calculate elapsed time between the first report and the timestamp we are considering
                            delta2 = current_second - first_second
                            # calculate the distance traveled from the first report to the position at
                            # the desired timestamp
                            dist = speed * delta2

                            # calculate the required fix, given the distance traveled and the initial
                            # bearing obtained in calc1
                            # noinspection PyUnresolvedReferences

                            lat, lon, bearing = direct_haversine(lat1 = p1.lat, lon1=p1.long, bearing = bp1p2, distance = dist)
                            
                            # calc2 = Geodesic.WGS84.Direct(lat1=p1.lat, lon1=p1.long, azi1=bp1p2, s12=dist)
                            # lat = calc2["lat2"]
                            # long = calc2["lon2"] 
                            # bearing = calc2["azi2"]
                            
                            # calculate the expected altitude using the elapsed time and the climb rate                            
                            fl = round( p1.fl + climb_rate * delta2, 2)                        

                        # calculate the next position in TIME_VECTOR seconds, used for charting
                        # check if this is really necessary
                        next_lat, next_lon, next_bearing = direct_haversine(lat1 = lat, lon1 = lon, bearing = bearing, distance = speed * TIME_VECTOR)

                        # speed in knots
                        speed_knots = speed * (3600 / 1852)
                        
                        # climb rate in feet per minute
                        climb_rate_fpm = climb_rate * (100 * 60) 

                        # speed in knots, vertical speed in feet per minute
                        result[current_second] = [lat, lon, fl, bearing, speed_knots, next_lat, next_lon, climb_rate_fpm]
                        current_second += 1
                else:
                    # the time difference between the reports is zero, no calculation will
                    # be done, advance to the next pair. Since the timestamp hasn't changed, no need
                    # to increment the second of reference
                    self.sametime += 1
                    # print (self.id,"\n", p1,"\n",p2)

        self.interpolated = result
        self.set_flight_direction_interpolated()

        # gravar aqui o dataset de interpolados, para comparar com os i
        # interpolados do dataset de teste, para validar o processo de interpolação.
    
    def has_interpolated(self, at_second: int) -> bool:
        """
        Returns true if the requested timestamp has been interpolated
        Args:
            seconds: requested timestamp
        """
        return self.interpolated and at_second in self.interpolated
    
    # calculate vertical speeds
    def calc_vert_speeds(self):
        if self.surveillance and len(self.surveillance)>=2:
            for n in range(0, len(self.surveillance)-1):
                r1 : Report = self.surveillance[n]
                r2 : Report = self.surveillance[n+1]
                delta = r2.seconds-r1.seconds                
                fl1 = r1.fl
                fl2 = r2.fl                
                # if fl1 != fl2:
                print(" End : {}  Start :{}   - Altitudes {} - {} = {}, {} feet/min".format(r2.seconds, r1.seconds, fl2, fl1, (fl2-fl1)*100, round((fl2-fl1)*100/delta*60)))            

    # TO DO #
    # see if still needed
    def is_under_surveillance(self, ts: int) -> bool:
        """
        Determine if a flight is under surveillance at a given time.
        For separation minima determination purposes.
        TBD, always returns true
        """
        # return self.adsb and (ts == 0)
        return True

    def check_proximity_t(self, other: Flight, ts: int, alt_min_dif : int = 0, alt_max_dif = ALT_THRESHOLD_1000, step : int = 1, speed :float = 1 ) -> Tuple[bool, bool, str, str, bool, float, float]:
        
        """
        Check if a flight interacts (is proximate) with another
        Args:
            other: the flight to check against
            t : timestamp to use as reference
            alt_min_dif : smallest altitute threshold to consider
            alt_max_dif : biggest altitute threshold to consider
        
        Returns tuple with 5 values:
            True if there's a vertical interaction, False otherwise
            True if there's a lateral interaction, False otherwise
            [OTS|MIX|RND] for OTS traffic, mixed or random traffic
            [SAMEDIR|RECIPROCAL] for traffic direction
            True if both flights overlap
        """

        # define default results        
        
        # initialize vertical pair for 15 min. longitudinal separation
        vertical_pair = False
        # initialize vertical pair for 120 NM longitudinal separation
        vertical_pair_120 = False
        
        lateral_pair = False
        overlap = False        
        direction = None        
        
        longitudinal_separation_nm = DEFAULT_LONGITUDINAL_SEP_NM
        longitudinal_separation_time = DEFAULT_LONGITUDINAL_SEP_TIME
        
        lateral_separation = DEFAULT_LATERAL_SEP

        # make sure both flights have interpolated reports for the required timestamp
        # should not be needed, since this function should be called only after checking that both flights have interpolated reports inside RVSM at the required timestamp
        
        if ts in self.interpolated and ts in other.interpolated:
            # position of this flight at the reference timestamp
            p1 = self.interpolated[ts]
            # altitude in feet of flight_i at the reference timestamp
            alt1: float = p1[2] * 100
            # position of the other flight at the reference timestamp
            p2 = other.interpolated[ts]
            # altitude in feet of flight_j at the reference timestamp 
            alt2: float = p2[2] * 100
            
            # calculate the relative angle between both flights, and caracterize them according to
            # PANS-ATM/DOC 7030/NAT DOC 008 - Application of separation minima
            angle = heading_diff(p1[3], p2[3])
            
            #TODO apply here the new direction classification based on the updated traffic types
            direction = SAMEDIR if angle < 90.0 else OPPOSITE

            # to change the threshold for HLA, use HLA_LOW and HLA_HIGH defined in init.py
            if HLA_LOW <= alt1 <= HLA_HIGH and HLA_LOW <= alt2 <= HLA_HIGH:
                # calculate difference between flight levels
                dfl = round(abs(alt1 - alt2), 0)

                # are the flights inside the allowed vertical range ?
                if alt_min_dif <= dfl <= alt_max_dif:
                    
                    # calculate the relative position of the flights, to determine if they are in the same area of the airspace
                    
                    # TODO calculate overlapping in longitudinal dimension
                    # project one flight's position in the other flight's route                    
                    # overlap_long = longitudinal distance between the pair is less than the sum of the both flight's length
                    
                    # Calculate the track-to-track distance between both flights, in NM,
                    distance_p1p2 = inverse_haversine(lat1 = p1[0], lon1 = p1[1], lat2 = p2[0], lon2 = p2[1])[0] / 1852
                    
                    # if using geo_wgs84.py
                    # calc1 = Geodesic.WGS84.Inverse(lat1 = p1[0], lon1=p1[1], lat2 = p2[0], lon2 = p2[1])
                    # distance_p1p2 = calc1["s12"] / 1852

                    # check if the flights are so far apart that they do not constitute a pair
                    if (direction == OPPOSITE and distance_p1p2 >= 400) or (distance_p1p2 >= 200):
                        # could be better coded to avoid 2 return instructions
                        return vertical_pair, lateral_pair, direction, overlap, longitudinal_separation_nm, lateral_separation

                    # check if the pair is closer than the biggest dimension of the two aircraft
                    # dimensions_nm = max(self.max_dimension, other.max_dimension)/1852
                    # dimensions_nm = 5 # try with 1NM
                    # if dimensions_nm >= distance_p1p2:
                    #   pass
                    
                    # review the calculation of the overlap distance
                    overlap_distance = speed / 3600 * step
                    
                    # determine if the flights are overlapping
                    if  distance_p1p2 <= overlap_distance:
                        overlap = True
                    
                    # Get the azimuth12 from f1 to f2 and the reverse azimuth21, from f2 to f1
                    # azimuth12 = mod(calc1["azi1"], 360)
                    # azimuth21 = mod(calc1["azi2"] + 180, 360)
           
                    # determine navigation performance to apply
                    # move from here to make sure it is calculated only once per pair of flights, and not for each timestamp
                    # lateral, precision, angle, direction, box_i, box_j, lateral_separation, longitudinal_separation = self.get_separation_with(other, ts=t)

                    # lateral = 'RNP4'
                    # precision = 'PBCS'
                    
                    # distance_i = p1[4] * 15 / 60
                    # distance_j = p2[4] * 15 / 60

                    # add code to calculate the longitudinal and lateral distances between two flights, to avoid the boxes.

                    # protected airspace for flight1
                    box_i = get_bounding_box_haversine(p = p1, lateral=lateral_separation, time_ahead = longitudinal_separation_time, time_behind = longitudinal_separation_time)
                    box_i_120 = get_bounding_box_haversine(p = p1, lateral=lateral_separation, dist = longitudinal_separation_nm, time_ahead = None, time_behind = None)
                    
                    # protected airspace for flight2
                    box_j = get_bounding_box_haversine(p = p2, lateral=lateral_separation, time_ahead = longitudinal_separation_time, time_behind = longitudinal_separation_time)
                    box_j_120 = get_bounding_box_haversine(p = p2, lateral=lateral_separation, dist = longitudinal_separation_nm, time_ahead = None, time_behind = None)
                    
                    # flag to indicate if the flights are separated by 1000', will be used for vertical occupancy
                    # one_fl = True if 900 <= dfl <= alt_max_dif else False
                    one_fl = True if alt_min_dif <= dfl <= alt_max_dif else False
                    
                    # Determine if proximate vertical pairs
                    # vertical_pair = False
                   
                    if one_fl:
                        """
                        # check for track to track distance,
                        # if the conditions are checked
                        if direction == SAMEDIR and precision == SEP_PBCS and lateral == SEP_RNP4 and self.adsb and other.adsb:
                            if distance_p1p2 <= ASEPS_TT + 1:
                                vertical_pair = True
                                lateral_separation = 15
                                longitudinal_separation = 15
                        else:
                            # the box definitions account for same or opposite direction
                            vertical_pair = is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i) or is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j)
                        
                        #if vertical_pair:
                            #print("vertical pair - {} @ {} seconds - {} at {} x {} at {}".format(vertical_pair, t, self.callsign, self.interpolated[t][2], other.callsign, other.interpolated[t][2]))
                        """
                        
                        # Determine if the flights are vertical pairs using the protected airspace boxes
                        # for both longitudinal separation criteria (120NM and 15 min.)
                        vertical_pair = is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i) or is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j)
                        vertical_pair_120 = is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i_120) or is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j_120)
                    
                    else:
                        # not a vertical pair
                        # print("Not a vertical pair")
                        pass

                    # if the flights are at the same altitude, determine lateral and longitudinal proximity (v1.0)
                    if dfl <= ALT_THRESHOLD_SAME:

                        # TODO determine if the flights are a longitudinal pair,
                        # using the protected airspace boxes, to avoid calculating the cross track distance for all pairs
                        # of flights at the same altitude, which is computationally expensive

                        # Sx for longitudinal pairs, to be reviewed, maybe add a margin to the distance condition
                        # 2*Sx for opposite direction, Sx for same direction,
                        # to be reviewed, maybe add a margin to the distance condition
                        
                        # lateral_pair = False
                        # determine if it is a parallel pair, using Atul's method
                        # LATERAL_SEPARATION_HB = 100 # try with 100 NM, to be similar to NAV Canada criteria for lateral pairs, to be reviewed

                        # longitudinal_distance = max(p1[4], p2[4]) * 15/60
                        #box_i_100 = get_bounding_box(p=p1, lateral=LATERAL_SEPARATION_HB, dist = distance_i, behind = distance_i)
                        lateral_pair = is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i) or is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j)

                else:
                    # print("MORE THAN 1000 FEET BETWEEN THE FLIGHTS ", self.callsign, " e ", other.callsign)
                    pass

            else:
                # at least one of the flights is outside HLA, no need to calculate the separation minima, as they will not be considered for vertical occupancy
                # print("AT LEAST ONE OF THE FLIGHTS IS OUTSIDE HLA ", self.callsign, " e ", other.callsign)
                pass

        # verify if the pair is considered as overlapping but not a vertical or lateral pair
        if not vertical_pair and overlap:
            pass

        return vertical_pair, lateral_pair, direction, overlap, longitudinal_separation_nm, lateral_separation #, longitudinal_separation_time


    """ # New method, to be reviewed, to determine if the flights are lateral pairs,
        box_i_27 = get_bounding_box(p=p1, lateral=27, dist = longitudinal_i, behind = longitudinal_i)
        box_i_33 = get_bounding_box(p=p1, lateral=33, dist = longitudinal_i, behind = longitudinal_i)
        lateral_pair = (not is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i_27) and is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i_33))

        if not lateral_pair:
            longitudinal_j = 15/60 * p2[4]
            box_j_27 = get_bounding_box(p=p2, lateral=27, dist = longitudinal_j, behind = longitudinal_j)
            box_j_33 = get_bounding_box(p=p2, lateral=33, dist = longitudinal_j, behind = longitudinal_j)
            lateral_pair =  (not is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j_27) and is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j_33))

            if not lateral_pair:
                box_i_56 = get_bounding_box(p=p1, lateral=56, dist = longitudinal_i, behind = longitudinal_i)
                box_i_63 = get_bounding_box(p=p1, lateral=63, dist = longitudinal_i, behind = longitudinal_i)
                lateral_pair = (not is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i_56) and is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i_63))

                if not lateral_pair:
                    box_j_56 = get_bounding_box(p=p1, lateral=56, dist = longitudinal_j, behind = longitudinal_j)
                    box_j_63 = get_bounding_box(p=p1, lateral=63, dist = longitudinal_j, behind = longitudinal_j)
                    lateral_pair = (not is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j_56) and is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_j_63))
                                
        if lateral_pair:
            # make sure the flights are paraller
            pass    
        
        # calculate cross track distance from P2 to the segment of P1
        distance_x_p2p1, lat_p2p1, long_p2p1, distance_a_p2p1 =x_track_fix(p1[0], p1[1], p1[5], p1[6], p2[0], p2[1])
        distance_x_p2p1 = abs(distance_x_p2p1 / 1852)

        # calculate cross track distances from P1 to the segment of P2
        distance_x_p1p2, lat_p1p2, long_p1p2, distance_a_p1p2 = x_track_fix(p2[0], p2[1], p2[5], p2[6], p1[0], p1[1])
        distance_x_p1p2 = abs(distance_x_p1p2 / 1852)
        # distance_a_p1p2 /= 1852
        

        # if the flights are at LAT_SEP plus margin
        # latsep = LAT_SEP[precision][lateral]
        latsep = lateral_separation

        lateral_margin = 3
        
        # makes sure that the flights are parallel
        # reevaluate the conditions for parallel pairs, maybe add a margin to the angle condition or bigger buffer to the distance condition
        if (latsep - lateral_margin < distance_x_p2p1 < latsep + lateral_margin) and (latsep - lateral_margin < distance_x_p1p2 < latsep + lateral_margin):
            # check if flight1 is inside the protected airspace of flight2, or viceversa
            lateral_pair = is_fix_inside(lat=p2[0], long=p2[1], fix_list=box_i) or is_fix_inside(lat=p1[0], long=p1[1], fix_list=box_j)
        """ 