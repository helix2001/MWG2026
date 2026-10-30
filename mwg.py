import locale
import csv
from module import *
from math import sqrt, pi
from utils import calc_relative_speed
from flight import Flight
import pandas as pd
from pandas import read_csv, DataFrame
from numpy import histogram, arange, ceil, sum, linspace, squeeze, array
import scipy.stats as sps
from statsmodels.distributions.empirical_distribution import ECDF
from actype import ACType, import_actype
import matplotlib.pyplot as plt
import numpy as np

# Constant values, from the handbook and SOG, 2023

Tr = 295 # time at incorrect tracks/GNE, minutes
Nr = 10  # total tracks crossed

Pz1000 = 7.8E-8
Pz0 = 0.48
lambda_xz = 0.036   # NM, can be determined empirically

MWG_speeds = [ 13/60 , 5/60 , 1.5/60 ]

T_Error = 273       # Time at incorrect levels, minutes
FnT = 2110330 * 60  # total flight time, minutes
Nc1 = 49            # Number of levels crossed at speeds < 4000'/min
Nc2 = 0             # Number of levels crossed at speeds > 4000'/min

Sx = 120            # 30 NM, longitudinal spacing between flights, must be revisited
                    # Can be determined empirically

TERM1 = Pz0 * T_Error / FnT

# this term is always 0 in this version, since Nc2 is considered to be 0
# term3 = (Nc2*(lambda_x**2 * (1+pi/4)+2*lambda_x*lambda_z)/(4*lambda_x*lambda_z) *
#   ((abs(rel_speeds[1])/(2*lambda_y) + sqrt(rel_speeds[0]**2+rel_speeds[1]**2)/lambda_xz)/kinetic_term))
TERM3 = 0

# Methods for executing MWG calculations
def kinetic_term_box(V : Vector3D = None, gs1 : float = 0.0, gt1 : float = 0.0, vs1 : float = 0.0, gs2 : float = 0.0 , gt2 = 0.0, vs2 : float = 0.0, wingspan : float = 0.0, length : float = 0.0, height : float = 0.0) -> float:
    """
    Calculate the kinetic term, box

    Args:
        gs1 (float, optional): Ground speed for flight 1. Defaults to 0.0.
        gt1 (float, optional): Ground track for flight 1. Defaults to 0.0.
        vs1 (float, optional): Vertical speed for flight 1. Defaults to 0.0.
        gs2 (float, optional): Ground speed for flight 2. Defaults to 0.0.
        gt2 (float, optional): Ground track for flight 2. Defaults to 0.0.
        vs2 (float, optional): Vertical speed for flight 2. Defaults to 0.0.
        wingspan (float, optional): Largest wingspan. Defaults to 0.0.
        length (float, optional): Largest length. Defaults to 0.0.
        height (float, optional): Largest height. Defaults to 0.0.

    Returns:
        float : Returns the kinectic term, modeled as a box
    """
    try:
        # considers vs = 0
        if V == None:
            V = calc_relative_speed(gs1 = gs1, h1 = gt1, vs1=vs1, gs2 = gs2, h2 = gt2, vs2 = vs2)    
        
        Vxy = sqrt((V[0])**2 + (V[1])**2)
        result = Vxy/(2*min(length, wingspan)) + (abs(V[2])/(2*height))
    
    except Exception as exception:
        result = 0
        print(exception)
    return result


def kinetic_term_cylinder(V : Vector3D = None, gs1 : float = 0.0, gt1 : float = 0.0,  gs2 : float = 0.0 , gt2 = 0.0, vs1:float=0, vs2 : float=0, length : float = 0.0, wingspan : float = 0.0, height : float = 0.0)->float:
    """
    Calculate the kinetic term, cylinder
    Args:
        gs1 (float, optional): _description_. Defaults to 0.0.
        gt1 (float, optional): _description_. Defaults to 0.0.
        gs2 (float, optional): _description_. Defaults to 0.0.
        gt2 (float, optional): _description_. Defaults to 0.0.
        dimxy1 (float, optional): _description_. Defaults to 0.0.
        dimxy2 (float, optional): _description_. Defaults to 0.0.
        dimz1 (float, optional): _description_. Defaults to 0.0.
        dimz2 (float, optional): _description_. Defaults to 0.0.
    Returns:
        float: _description_
    """
    try:
        if V == None:
            V = calc_relative_speed(gs1=gs1, gt1=gt1, gs2=gs2, gt2=gt2, vs1=vs1, vs2 = vs2)    
        Vxy = sqrt(V[0]**2 + V[1]**2)
        result = ((2*Vxy)/(pi*min(length, wingspan))) + (V[2]/(2*height))
    except:
        result = None
    return result

def calc_py0(f1 : Flight, f2 : Flight) -> float:
    """
    Calculate py0 of two flights.
    Uses the list of interpolated points for each flight
    Is this irrelevant for random traffic ???
    """
    try:
        # get the wider wingspan
        WINGSPAN = max(f1.acdimensions.wingspan, f2.acdimensions.wingspan)/1852
    
        # get the ctes of both flights, from the interpolated list
        ctes = f1.ctes
        ctes.extend(f2.ctes)
        
        # determine the empirical cumulative distribution function for the CTEs
        data = DataFrame(ctes).to_numpy()
        ecdf = ECDF(data.T[0])
        
        # get the number of bins to interpolate
        min_cte = min(data)[0]
        max_cte = max(data)[0]
        count = int((max_cte-min_cte) / 0.001)
        bins = linspace(min_cte,max_cte,count)
        bins = array(list(zip(bins,bins[1:])))
        
        result =  sum(list(map(lambda x : (ecdf (x[1] + WINGSPAN) - ecdf(x[0] - WINGSPAN)) * (ecdf (x[1]) - ecdf (x[0])) , bins)))

    except Exception as error:
        result = 0
        with open('errors.txt','a') as f:
            f.write('ERROR on PY0 calc:{} {} {} {}  {}\n'.format(f1.callsign,f1.actype,f2.callsign,f2.actype,error))
        f.close()
    return result

def calc_values_ij(i:Flight, j : Flight, step : int = 1, alt_min = 0, alt_max = ALT_THRESHOLD_1000):

    # time in seconds that the flights are proximate in the vertical, lateral and overlap dimensions, to be used for occupancy calculation
    prox_time_vert = 0
    prox_time_lat = 0
    prox_time_overlap = 0
    
    # total known flight time for the pair of flights
    total_pair_time = 0

    # first second and last second that the flights are proximate in any of the dimensions,
    # not necessarily the same as the first and last second of interaction,
    # since they might have moments of proximity in between moments of non-proximity 
    
    first_proximate = -1
    last_proximate = -1

    # First and last second that BOTH flights have interpolated data, which is not necessarily the same as
    # the first and last second of the flight time, since we might not have data for the whole flight time   
    
    start = 0
    finish = 0

    # Pz, represents the probability of a vertical overlap, calculated at every second
    Pz = 0.0
    
    # Collision  risk values for the pair, calculated at every second,
    # representing the various dimensions to be summed at the end of the method.
    CRij_overlap = 0.0
    CRij_vertical = 0.0
    CRij_lateral = 0.0

    # Occupancy values for the pair, in the 3 dimensions, calculated at the end of the method, using the proximate times calculated at every second
    occupancy = 0.0
    occupancy_lat = 0.0
    occupancy_vert = 0.0
    occupancy_overlap = 0.0
    
    # calculate the relative speed between the flights, using the interpolated points, at every step second,
    relative_speeds = []
    average_speeds = [None, None, None]

    # determine the relative direction of the flights, to determine the appropriate occupancy formula, and for analysis purposes
    opposite_counts = 0
    samedir_counts = 0
    total_counts = 0

    # global direction between the flights, to be determined at the end of the method, based on the relative direction at every second, for analysis purposes
    direction = ''
    
    # default value for py0, in case the calculation fails, to avoid errors in the risk calculation
    py0 = 0.0
    
    # calc_values = DataFrame(columns = ['Second','Vertical','Lateral','Overlap','Pzt','CRij_t','Py0','KineticTerm','Sx','Sy','Direction','CRij_lateral'])
    if i and j:
        # implement a check to see if the flight are in the same altitude range,
        # if not, we can skip the pair, since they cannot interact
        # the check currently is implemented in the calling method,
        # but it can be implemented here as well, to be more efficient,
        # since we can skip the pair before calculating the relative speeds,
        # which is the most computationally expensive part of the method.

        pd_i = pd.DataFrame(i.interpolated.values(), columns = ['Second','Latitude','Longitude','GroundTrack','GroundSpeed','Altitude','VerticalRate','CTE'])
        pd_j = pd.DataFrame(j.interpolated.values(), columns = ['Second','Latitude','Longitude','GroundTrack','GroundSpeed','Altitude','VerticalRate','CTE'])

        pd_i.to_csv(i.callsign+'.csv',sep=';',decimal=',')
        pd_j.to_csv(j.callsign+'.csv',sep=';',decimal=',')

        track = RANDOM if i.ots == "0" and j.ots == "0" else OTS if i.ots == "1" and i.ots == "1" else MIX

        # check here if the flights have interpolated data, if not, we cannot calculate the relative speeds and occupancy values, so we can skip the pair
        i_seconds = list(i.interpolated.keys())
        j_seconds = list(j.interpolated.keys())
        
        seconds = sorted(set(i_seconds) & set(j_seconds))
        
        # make sure we have at least step seconds of data for both flights,
        # otherwise we cannot calculate the occupancy values, since they are based on the proximate time,
        # which is calculated at every step second

        if len(seconds) >= step:
            
            start = seconds[0]
            finish = seconds[-1]
            
             # determine the time of flight which we have data for both flights.        
            total_pair_time = (i.elapsed_time_surveillance + j.elapsed_time_surveillance) / step
            
            # calculate max of aircraft dimensions, in NM
            lambda_x = max(i.acdimensions.length, j.acdimensions.length) / 1852
            lambda_y = max(i.acdimensions.wingspan, j.acdimensions.wingspan) / 1852
            lambda_z = max(i.acdimensions.height, j.acdimensions.height) / 1852
                
            py0 = float(i.py0_with(j))

            data = []

            #  takes a report at every step second.
            for second in range(start, finish + 1, step):
                # calculate the number of times the iteration is called
                # calc_values_ij.iterations += 1

                if second == 1754012351:
                        pass
                
                total_counts += 1

                # get ground speeds, NM/H                    
                gs_i = i.interpolated[second][4]
                gs_j = j.interpolated[second][4]

                # get ground tracks
                gt_i = i.interpolated[second][3]
                gt_j = j.interpolated[second][3]

                # get vertical speeds, ft/min, convert to NM/H
                # TODO can be optimized by calculating the conversion factor once,
                # since it is always the same
                vs_i = i.interpolated[second][7] * 0.3048 *60 / 1852
                vs_j = j.interpolated[second][7] * 0.3048 *60 / 1852
                
                # calculate relative speed components for the pair, all in Knots
                relative_speeds_pair = calc_relative_speed (gs1 = gs_i, h1 = gt_i, vs1 = vs_i, gs2 = gs_j, h2 = gt_j, vs2 = vs_j)
                
                # calculate the relative ground speed, to be used for the proximity check, in Knots
                relative_ground_speed = sqrt(relative_speeds_pair.x**2 + relative_speeds_pair.y**2)

                # append relative speeds to the total relative speeds array for the  pair of flights
                relative_speeds.append([relative_speeds_pair.x, relative_speeds_pair.y, relative_speeds_pair.z])
                        
                vertical, lateral, direction, overlap, Sx, Sy  = i.check_proximity_t(other = j, ts = second, alt_min_dif = alt_min, alt_max_dif = alt_max, speed = relative_ground_speed, step=step)

                if direction == OPPOSITE:
                    opposite_counts +=1

                else: #direction == SAMEDIR
                    samedir_counts += 1
                    
                if vertical or lateral or overlap:
                    
                    # save moments of first and last interaction
                    first_proximate = second if first_proximate == -1 else first_proximate
                    last_proximate = second if second > last_proximate else last_proximate                            
                        
                    # increment the number of events of the appropriate proximity
                    # global_occupancy_events +=1                  
                    # move it below, to make it more efficient,
                    # since we only need to calculate it if there is proximity in at least one of the dimensions

                    # kinetic_term_old = abs(rel_speeds.x)/(2*lambda_x)+ abs(rel_speeds.y)/(2*lambda_y) + abs(rel_speeds.z)/(2*lambda_z)

                    # calculate kinetic term, using the predefined speeds 
                    kinetic_term = kinetic_term_box( V= relative_speeds_pair, gs1 = gs_i, gt1 = gt_i, gs2 = gs_j, gt2 = gt_j, wingspan = lambda_y, length = lambda_x, height = lambda_z, vs1=vs_i, vs2=vs_j)
                
                    # CRij_t = kinetic_term
                
                    # TERM1 is a constant, calculated above = Pz0*T_Error/FnT
                    term2 = (Nc1 * 2 * lambda_z )/(FnT*abs(relative_speeds_pair.z)) if relative_speeds_pair.z != 0 else 0

                    Pz_t = Pz1000 + TERM1 + term2 + TERM3
                    Pz += Pz_t

                    CRij_t = (Pz_t * ((lambda_x / Sx) if Sx !=0 else 1) * kinetic_term)

                    if overlap:
                        CRij_overlap += CRij_t
                        prox_time_overlap += 1
                
                    if vertical:
                        CRij_vertical += CRij_t
                        prox_time_vert += 1

                    term = None
                    if lateral:
                        term = py0 * Tr/FnT + (Nr*(2*lambda_y)/(abs(relative_speeds_pair[1])*FnT) if abs(relative_speeds_pair[1]) !=0.0 else 0)
                        CRij_lateral_t = Pz0 * term * (lambda_x/Sx) * kinetic_term
                        CRij_lateral += CRij_lateral_t
                        prox_time_lat += 1
                

                    data.append([second, vertical, lateral, overlap, kinetic_term, term2, Pz_t, 
                                 CRij_t, py0, term, CRij_lateral_t])

            data = DataFrame(data, columns = ['Second','Vertical','Lateral','Overlap','KineticTerm','Term2','Pz_t','CRij_t','Py0','Term','CRij_lateral'])
            data.to_csv('individual.csv',sep=';',decimal=',')

            # determine relative directions of the flights
            direction = OPPOSITE if  opposite_counts >= samedir_counts else SAMEDIR

            # calculate Ez_ij = (2*TP_ij)/(Ti+Tj)
            occupancy_vert = (prox_time_vert * 2) / total_pair_time
            occupancy_lat = (prox_time_lat * 2) / total_pair_time
            occupancy = ((prox_time_lat + prox_time_vert) * 2) / total_pair_time
        
            # calculate overlap factor Oz_ij = (2*Ot_ij)/(Ti+Tj)
            # might need correction for opposite direction traffic
            occupancy_overlap = ( prox_time_overlap * 2 ) / total_pair_time 
                
            # calculate average speeds
            average_speeds = np.mean(relative_speeds, axis = 0)

            # if len(calc_values)>0:
                #  calc_values.to_csv(i.callsign+'-'+j.callsign+'.csv',sep=';',decimal='.')

        else:
            pass
            # print(i.id,' ',j.id, " do not interact !")            
    
    # returns vertical, occupancy, lateral occupancy, timestamp of first proximity, timestamp of last proximity, total overlap time
    return occupancy, occupancy_vert, occupancy_lat, occupancy_overlap, start, finish,  first_proximate, last_proximate,\
        CRij_overlap, CRij_vertical, CRij_lateral, Pz, average_speeds, direction, py0, total_pair_time * step, \
            prox_time_lat * step, prox_time_vert * step, prox_time_overlap * step


def calc_CR(py0 : float = 0.0, dimensions : Vector3D = (0,0,0), speeds : Vector3D = (0,0,0), Sx : float = 120.0, occupancy : float = 0.0) -> float:
    
    result = Pz1000 * py0 * (dimensions.x/Sx) * occupancy *((speeds.x/2*dimensions.x)+(speeds.y/2*dimensions.y)+(speeds.z/2*dimensions.z))
    
    return result


# average wingspan for heavy aircraft is 0.03 NM
def calc_py0_list(ctes:list, WINGSPAN = 0.03) -> tuple[float, float]:
    # review how to calculate py0 with the real wingspan contribution
    """
    NUM_BINS = 1000
    # definition of an averagewingspan value
    print('-----------------------\nReading file .')
    print('Creating histogram')

    values, bins, patches = plt.hist(x=ctes, bins=NUM_BINS)
    maxvalue = values.max()

    plt.ylim(top = maxvalue + 10000)
    plt.xlabel('SLOP')
    plt.ylabel('Absolute count')
    plt.title('SLOP usage in LPPO, 2022')
    plt.show()
    plt.clf()
    res = sps.relfreq(ctes,numbins=NUM_BINS)

    x = res.lowerlimit + linspace(0, res.binsize*res.frequency.size,res.frequency.size)
    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(x, res.frequency, width=res.binsize)
    ax.set_title('Relative frequency histogram')
    ax.set_xlim([x.min(), x.max()])
    fig.show()

    plt.clf()
    """
    data = DataFrame(ctes).to_numpy()
    min_cte = min(data)[0]
    max_cte = max(data)[0]

    ecdf = ECDF(data.T[0])
    # print(min_cte, ' ', max_cte)
    count = int((max_cte-min_cte) / 0.0001)

    # plt.plot(ecdf.x, ecdf.y)
    # plt.show()
    # print('Create X vector {}'.format(count))

    steps = linspace(min_cte,max_cte,count)
    # print(steps)
    steps = zip(steps,steps[1:])
    npa = array(list(steps))
    
    # steps = zip(npa, npa[1:])
    
    # print('Calculating py0same')
    # py0same = sum(list(map(lambda x : (ecdf (x[1]+WINGSPAN) - ecdf(x[0]-WINGSPAN)) * (ecdf(x[1])-ecdf(x[0])) , npa)))
    # print('Calculating py0opposite')
    # py0opp = sum(list(map(lambda x:(ecdf((-1*x[1])+WINGSPAN)-ecdf((-1*x[0])-WINGSPAN)) * (ecdf(x[1])-ecdf(x[0])) , npa)))

    # print('Summing py0same')
    # py0same_dir = sum(py0same)
    # print(py0same_dir)
    # print('Summing py0opposite')
    # py0opposite_dir = sum(py0opp)
    # print(py0opposite_dir)
    # print('Done')
    # return py0same, py0opp

    py0 = sum(list(map(lambda x : (ecdf (x[1] + WINGSPAN) - ecdf(x[0] - WINGSPAN)) * (ecdf (x[1]) - ecdf (x[0])) , npa)))

    return py0


def calc_Pxy0(f1:Flight, f2:Flight) -> float:
    pass

def calc_py0_list(ctes:list, WINGSPAN = 0.03)->tuple[float,float]:
    """
    Calculate py0 from a list of CTE

    Args:
        ctes (list): List of CTEs
        WINGSPAN (float, optional): Average wingspan to consider. Defaults to 0.03.

    Returns:
        tuple[float,float]: Returns py0 for samedir and opposite
    """

    data = DataFrame(ctes).to_numpy()
    ecdf = ECDF(data.T[0])
        
    # get the number of bins to interpolate
    min_cte = min(data)[0]
    max_cte = max(data)[0]
    count = int((max_cte-min_cte) / 0.001)
    bins = linspace(min_cte,max_cte,count)
    bins = array(list(zip(bins,bins[1:])))
        
    # show the ecdf
    # plt.plot(ecdf.x, ecdf.y)
    # plt.show()
    py0_same =  sum(list(map(lambda x : (ecdf (x[1] + WINGSPAN) - ecdf(x[0] - WINGSPAN)) * (ecdf (x[1]) - ecdf (x[0])) , bins)))
    py0_opp =  sum(list(map(lambda x : (ecdf (x[1] - WINGSPAN) - ecdf(x[0] + WINGSPAN)) * (ecdf (x[1]) - ecdf (x[0])) , bins)))
                  
    return py0_same, py0_opp
    

# Set locale to the user's default (system settings)
locale.setlocale(locale.LC_ALL, '')
current_locale = locale.localeconv()
print(f"Locale successfully set to: {current_locale}")



pass