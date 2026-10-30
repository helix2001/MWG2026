import datetime
from collections import namedtuple

# named tuple for 3D calculations
# can it be replaced by numpy array for better performance in vectorized operations ?
Vector3D = namedtuple('ThreeD',['x','y','z'])
Vector3D.__doc__ = """ Tuple that represents a 3D vector """

# ANSP ID
ICELAND  = 0
UK       = 1
CANADA   = 2
NEWYORK  = 3
PORTUGAL = 4

# default separation minima, in NM or minutes, depending on the context
DEFAULT_LONGITUDINAL_SEP_TIME = 15
DEFAULT_LONGITUDINAL_SEP_NM = 120
DEFAULT_LONGITUDINAL_SEP_M = DEFAULT_LONGITUDINAL_SEP_NM * 1852

# modifiers for lateral separation, in NM

# requirement v1.0, 3.2
GENTLE_SLOPE = 5
SLOP         = 2
DEFAULT_LATERAL_SEP = 60
DEFAULT_LATERAL_SEP_MIN = DEFAULT_LATERAL_SEP - GENTLE_SLOPE - SLOP
DEFAULT_LATERAL_SEP_MAX = DEFAULT_LATERAL_SEP + GENTLE_SLOPE + SLOP

# for calculating seconds from midnight
MIDNIGHT_STR = '1970-01-01 '
MIDNIGHT = datetime.datetime(year = 1970, month = 1, day = 1, hour=0, minute = 0, second = 0, microsecond=0)

# define the names of the fields / dictionary keys
# for importing data from CSV files
ID = "VOOID"  # internal flight id / primary key
CALLSIGN = "CALLSIGN"
DEPARTURE = "DEP"
DESTINATION = "DEST"
CODE = "CODE"  # Mode-S / ADS-B hex code
EQUIP10A = "EQUIP10A"
EQUIP10B = "EQUIP10B"
PBN = "PBN"
REG = "REG"
SURV = "SUR"
SSR = "SSR"
PBCS = "PBCS"
FLIGHTRULES = "FR"
TIPO = "TIPO"
RNP4 = "RNP4"
RNP10 = "RNP10"
OTS = "OTS"
ADSB = "ADSB"
MOPS = 'MOPS'
ACTYPE = 'ACTYPE'
SIC = "SIC"
SAC = "SAC"
WTC = "WTC"

CTE = 'CTE'
PROJ_LAT = 'PROJ_LAT'
PROJ_LON = 'PROJ_LON'

LAT = "LAT"
LONG = "LONG"
FL = "FL"
HEXCODE = "CODE"
GT = "GT"
GS = "GS"
TIMESTAMP = "TIMESTAMP"
SECONDS = "SECONDS"
SLOP = "SLOP"

# FOX Process v1.0
# traffic type
SAMEDIR = 0
CROSSING = 1
OPPOSITE = 2
RECIPROCAL = 3
SAME_PARALLEL = 4
OPP_PARALLEL = 5 

TRAFFIC_TYPE = ['SAME','CROSSING','OPPOSITE','RECIPROCAL','SAME_PARALLEL','OPP_PARALLEL']

# flight's direction
EASTBOUND = 0
WESTBOUND = 1
NORTHBOUND = 2
SOUTHBOUND = 3

DIRECTION = ['EASTBOUND','WESTBOUND','NORTHBOUND','SOUTHBOUND']

#OTS
OTS = 0
RANDOM = 1
MIX = 2
TRACK = ['O/O','R/R','O/R']

# NO OCCUPANCY CALCULATED
NO_OCCUP = "-"

# time vector for look ahead, in seconds. Currently 10 minutes
# used in graphical representations and calculations for look-ahead time
TIME_VECTOR = 600

# FOX process v1.0
# parallel route threshold, in degrees
# maximum bearing difference between two tracks for them to be considered as parallel
PARALLEL_THRESHOLD = 3.0

# FOX process v1.0
# altitude thresholds

ALT_THRESHOLD_SAME = 400.0
ALT_THRESHOLD_1000 = 1600.0

# Initial timestamp, seconds from midnight (uh ?)
REFERENCE_TIMESTAMP = 43200

# Default time span, seconds (uh ?)
REFERENCE_SPAN = 3600


# FOX process v1.0
# HLA altitudes
HLA_LOW = 29000 - ALT_THRESHOLD_SAME/2
HLA_HIGH = 41000 + ALT_THRESHOLD_SAME/2

# Status for opposite direction traffic
# define as integer, will make the computations faster ???
BEFORE = 0
AFTER = 1
PASSING_STATUS = ["BEFORE_PASSING", "AFTER_PASSING"]

# FOX process v1.0
# separation minima descriptions

# VHF coverage
SEP_VHF = 0

# lateral
SEP_RNP4 = 1
SEP_RNP10 = 2
SEP_HLA = 3
SEP_GNSS = 4

# PBCS implies CPDLC connection existed
SEP_PBCS = 5
SEP_NONPBCS = 6   

# SURV implies PBCS, RNP4 and (surveillance reports or considering ADSB flag from the flight plan
SEP_SURV = 7

SEP = ['VHF', 'RNP4', 'RNP10', 'HLA', 'GNSS', 'PBCS', 'NONPBCS', 'SURV']

# Dictionaries containing separation minima
# negative values represent minutes,
# positive values represent nautical miles

LAT_SEP = {
    SEP_PBCS: {SEP_RNP4: 23, SEP_RNP10: 50, SEP_HLA: 60},
    SEP_NONPBCS: {SEP_RNP4: 50, SEP_RNP10: 50, SEP_HLA: 60},
    SEP_SURV: {SEP_RNP4: 19, SEP_RNP10: 50, SEP_HLA: 60}}

# will serve for same direction traffic
LONGITUDINAL_DICT = {
    SEP_PBCS: {SEP_RNP4: 30, SEP_RNP10: -5, SEP_HLA: -10},
    SEP_NONPBCS: {SEP_RNP4: -10, SEP_RNP10: -10, SEP_HLA: -10},
    SEP_SURV: {SEP_RNP4: 17, SEP_RNP10: -10, SEP_HLA: -60}}

LONG_SEP = {
    SAMEDIR: {
        BEFORE: LONGITUDINAL_DICT,
        AFTER: LONGITUDINAL_DICT},                   
    
    RECIPROCAL: {
        # separations before the traffic passes each other, 15 minutes before the passing point
        # in all cases
        BEFORE: {
            SEP_PBCS: {SEP_RNP4: -15, SEP_RNP10: -15, SEP_HLA: -15},
            SEP_NONPBCS: {SEP_RNP4: -15, SEP_RNP10: -15, SEP_HLA: -15},
            SEP_SURV: {SEP_RNP4: -15, SEP_RNP10: -15, SEP_HLA: -15}},
        # separations after the traffic passes each other
        AFTER: {
            SEP_PBCS: {SEP_RNP4: 30, SEP_RNP10: 50, SEP_HLA: -10},
            SEP_NONPBCS: {SEP_RNP4: -10, SEP_RNP10: -10, SEP_HLA: -10},
            # SEP_NONPBCS: {SEP_RNP4: -1, SEP_RNP10: -1, SEP_HLA: -1},
            SEP_SURV: {SEP_RNP4: 5, SEP_RNP10: -10, SEP_HLA: -10}}}}

# VHF, surveillance, track to track, NM
TT_VHF = 5

# SURVEILLANCE, RCP240, track to track, NM
TT_ASEPS = 15

# NON-SURVEILLANCE, PBCS, RNP4, track to track, NM
PBCS_RNP4_TT = 30

# NON-SURVEILLANCE, PBCS, RNP10, track to track, NM
# Average 5 minutes at M080
PBCS_RNP10_TT = 40 

# NON-SURVEILLANCE, NONPBCS, RNP10, track to track, NM
RNP10_TT = 50

# FOX process v1.0
# ocuppancy types
VERTICAL = 0
LATERAL = 1
LONGITUDINAL = 2
OCCUPANCY = ['VERTICAL', 'LATERAL', 'LONGITUDINAL']

OO  = "OO"
RR  = "RR"
OR  = "OR"

OPP = 5
SAME = 6,
COMBINED = 7

MIN_CTE_SLOP = -0.5
MAX_CTE_SLOP = 2.5