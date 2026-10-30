print ('start imports !')
from os import path
import re
from csv import DictReader
from datetime import datetime as dt

# from module import *
from time import perf_counter
from functools import reduce
print ('import pandas !')
import pandas as pd
print ('import numpy !')
from numpy import histogram, arange, ceil, sum, linspace, squeeze, array, asarray
import scipy.stats as sps
from statsmodels.distributions.empirical_distribution import ECDF

print('import actype')
from actype import ACType, import_actype, aircraft_types
print('import utils')
import utils
# from utils import get_command_parameters
print('import import_data')
from import_data import import_flights, process_flights
print('import actype')
from mwg import calc_values_ij, calc_py0, Pz1000,  Pz0, FnT, T_Error, Nc1, Nc2, lambda_xz, MWG_speeds, Tr, Nr
#print('import charts')
#from charts import do_chart_display, plot_flights, start_chart_display, plot_flight_interpolated
print('import flights')
from flight import *

print('import matplotlib')
import matplotlib.pyplot as plt
print('import cartopy')
import cartopy.crs as ccrs
print('import math')
from math import comb
print('import sys')
import sys
print ('done imports !')

# default report step number of reports
REPORT_STEP = 5

# change this value to True to redirect the output from the console to a file called 'terminal.txt
REDIRECT_TO_FILE = False
if REDIRECT_TO_FILE:
    sys.stdout = open('terminal.txt','w')

"""
# replace with the drive where the data repository is located
DRIVE = '.'
SAMPLE_FILENAME = 'data/canada_sample.csv'
# path to the file in the data repository
FILENAME = DRIVE+'\\'+ SAMPLE_FILENAME
"""

# FILENAME = 'NAVP_2025-08-01.csv'
# FILENAME = r'E:\MWG_data\Canada_TBCRM_Data_Aug7_2025.csv'
FILENAME = 'NAVP_LATERAL.csv'

# filter contains a list of flight ids to process
# filter = [1790943,1790923,1790983,1790982, 1790996] 

# make sure that the list called filter exists
if not 'filter' in locals():
        filter = []
        # filter = [1740474,1741251,1740873,1740977]

def setup_filenames():
    filename, outfile = utils.get_command_parameters()
    if not filename:
        filename = FILENAME
    if not outfile:
        outfile = path.splitext(filename)[0]+'.pairs.csv'

    # determine the center, taking into account the filename
    f = filename.upper()
    if 'CANADA_' in f:
        source = CANADA
    elif 'ICELAND_' in f:
        source = ICELAND
    elif 'PORTUGAL_' in f:
        source = PORTUGAL
    elif 'NAVP' in f:
        source = PORTUGAL
    elif 'ZNY_' in f:
        source = NEWYORK
    elif 'UK_' in f:
        source = UK
    else:
        source = None

    return filename, outfile, source

if __name__ == '__main__':

    filename, outfile, source = setup_filenames()
    
    # use the 5th position report for the UK, CANADA and ICELAND (surveillance),
    # and all position reports for NY and Santa Maria
    if source in (NEWYORK,PORTUGAL):
        step = 1
    else:
        step = REPORT_STEP

    st = perf_counter()
    print (" Starting import of flights")
    flight_list, flights_second, results_filename = import_flights(filename, filter = filter, report_step = step, ANSP = source)
    print(f'Finished importing flights, took {perf_counter()-st} !')


    flight_csv = []
    columns = ['ID','CALLSIGN','ELAPSED_SURVEILLANCE(H)','ELAPSED_PROFILE(H)','ACTYPE','WTC','PBCS','CODE','OTS','PROFILE_REPORTS','SURVEILLANCE_REPORTS','INTERPOLATED_REPORTS',
               'MIN_FL','MAX_FL','ENTRY_LAT','ENTRY_LONG','ENTRY_TIME','EXIT_LAT','EXIT_LONG','EXIT_TIME','SURVEILLANCE_START','SURVEILLANCE_FINISH']
    
    print ('applying filters')
    # filter the flights list based on altitudes
    
    """
    if len(filter)>0:
        new_flights = { id:flight for id, flight in flight_list.items() if flight.id in filter and flight.acdimensions != None and len(flight.interpolated) != 0  and flight.max_fl >= 288.00 and flight.min_fl <= 412.00}
    else:
        new_flights = flight_list
    """

    discarded_flights = {}
    usable_flights = {}

    for i in flight_list:
        flight : Flight = flight_list[i]

        description = flight.get_description()
        if description != None:
            flight_csv.append(description)

        profile_fixes = list(map(lambda a:[flight.id, a.lat, a.long, a.timestamp_bin], flight.profile))
        surveillance_fixes = list(map(lambda a:[flight.id, a.lat, a.long, a.timestamp_bin, a.fl,a.cte], flight.surveillance))
        interpolated_fixes = list(map(lambda a,b :[flight.id, a[0], a[1], dt.fromtimestamp(b), a[2]], flight.interpolated.values(), flight.interpolated.keys()))

        if len(surveillance_fixes) == 0:
            print(f'Flight with id {i} and callsign {flight.callsign} was discarded, contains no surveillance reports.')
            continue

        if (filter == [] or flight.id in filter) and len(flight.interpolated) != 0  and flight.max_fl >= 288.00 and flight.min_fl <= 412.00:
            usable_flights[i] = flight
        else:
            discarded_flights[i] = flight
            print(f'Flight with id {i} and callsign {flight.callsign} was discarded.')
            if len(flight.profile) == 0:
                print('\tUnable to load cleared profile')
            if len(flight.interpolated) == 0:
                print(f'\tUnable to create interpolated profile.')
            
            flight.set_min_max_fl()

            if flight.max_fl < 288.0:
                print(f'\tThe flight was always below RVSM.')
            if flight.min_fl>412.0:
                print(f'\tThe flight was always above RVSM.')  
    
    pd.DataFrame(flight_csv,columns=columns).to_csv('flights.csv', index=False, sep=';')

    """
    SHOW_CHART = False
    if SHOW_CHART and len(filter)<20:
        m = start_chart_display()
        for i in filter:
            # plot_flight_interpolated(usable_flights[i],-1,86399,m)
            pass

        plot_flight_interpolated(usable_flights[1787844], 1659450829,	1659451224, m)
        plot_flight_interpolated(usable_flights[1787848], 1659450829,	1659451224, m)

        plt.show()
    """

    print("Calculate total flight time !")
    flights = list(usable_flights.values())

    flight_count = len(flights)
    if flight_count <= 1:
        print ('To calculate pairs of proximate flights, at least 2 flights are required. Not enough flights, stopping execution.')
        exit(1)

    # Create a dataframe to hold the pairs of flights that are proximate, with the relevant information for each pair, to be saved later on as a csv file
    # Maybe replace with a list, to avoid the overhead of pandas, and convert to dataframe at the end.
    pairs = pd.DataFrame(columns=['PAIR_DIRECTION','TRACK','ID_1','CALLSIGN_1','TOTAL_TIME_1 (Sec)','ID_2','CALLSIGN_2','TOTAL_TIME_2 (Sec)',
                                  'START_TIME','FINISH_TIME','PROX_START','PROX_FINISH','dVx (Knots)','dVy (Knots)','dVz (Knots)',
                                  'PY0','PY0_OLD','Pz','TIME_OVERLAP (Sec)','TIME_LATERAL (Sec)','TIME_VERTICAL (Sec)','OCCUP','OCCUP_VERT','OCCUP_LAT',
                                  'OCCUP_OVERLAP','CRij_OVERLAP','CRij_VERT','CRij_LAT'])

    sumCR_overlap = 0.0
    sumCR_vertical = 0.0
    sumCR_lateral = 0.0

    # performance calculations
    c = 1
    time_spent = 0
    time_of_start = perf_counter()
    
    # calculate number of possible pairs
    combs = comb(flight_count, 2)

    # dataframe to hold the computed global results
    results = []
        
    # variable to hold the dimensions of the flights
    dimensions = []

    # calculate average dimensions
    for i in flights:
        actype = get_actype(i.actype)
        if actype.wtc == 'ALL':
            print(f'Flight {i.id}, aircraft type {i.actype} not known, using {actype}')
        
        dim = [i.elapsed_time_surveillance /3600, i.acdimensions.wingspan/1852, i.acdimensions.length/1852, i.acdimensions.height/1852, i.average_speed_interpolated()]
        # print('Flight id:{} ; Flight acid:{} ; Flight time:{} hours ; Dimensions:{} ; AC Type:{}; Av.Horz.Speed {}'.format(i.id, i.acid, round(i.elapsed_time_surveillance()/3600,2), dim[1:4], i.actype, i.average_speed_interpolated()))
        dimensions.append(dim)
    
    mean_dimensions = asarray(dimensions).mean(axis=0)
    
    # calculate total flight time and average flight time per flight
    total_flight_time = reduce(lambda a, b : a + b, list( map( lambda a : a.elapsed_time_surveillance, flights)))
    hours_per_flight = round(total_flight_time/3600/flight_count,2)
        
    print(f'Total flight time: {total_flight_time} seconds; {round(total_flight_time/3600,2)} hours; { hours_per_flight} hours/flight')

    # record the global results calculated so far, to be saved later on as a csv file
    results.append(['Flight count',flight_count])
    results.append(['Total flight time (hours)',round(total_flight_time/3600,2)])
    results.append(['Mean flight time (hours)',mean_dimensions[0]])
    results.append(['Mean lambda_x',mean_dimensions[2]])
    results.append(['Mean lambda_y',mean_dimensions[1]])
    results.append(['Mean lambda_z',mean_dimensions[3]])
    results.append(['Mean Vxy',mean_dimensions[4]])    
    
    total_time_lat_vert = 0
    total_flight_time = 0
    total_time_lateral_pairs = 0
    total_time_vertical_pairs = 0
    total_time_overlap = 0
    total_py0 = 0

    ALT_MAX = 1100 # maximum altitude difference to consider for the calculations, in feet
    calc_values_ij.iterations = 0

    # """ remove the hashtag to comment out the plotting section if needed
    # FOX process v1.0
    # Plot the routes of all usable flights using Lambert Conformal Conic projection
    
    fig = plt.figure(figsize=(10, 6))
    ax = plt.axes(projection=ccrs.LambertConformal(central_longitude=-30, standard_parallels=(17, 51)))
    for flight in flights:
        if flight.interpolated and len(flight.interpolated) > 1:
            lats = [v[0] for v in flight.interpolated.values()]
            lons = [v[1] for v in flight.interpolated.values()]
            ax.plot(lons, lats,  alpha=0.7, transform=ccrs.PlateCarree())
    ax.set_title("Flight Routes (Interpolated) - Lambert Conformal Conic")
    ax.legend(loc="best", fontsize="medium", ncol=2)
    ax.gridlines(draw_labels=True)
    plt.tight_layout()
    plt.show()
    # """ remove the hashtag to comment out the plotting section if needed

    # interval between successive interpolated reports
    TIME_STEP = 1

    print ('Start collision risk calculations!')
    for i in range(0, flight_count - 1):    
        flight_i: Flight = flights[i]
        
        # get dimensions of the flight, if not already done
        if flight_i.acdimensions == None:
            flight_i.acdimensions = get_actype(flight_i.actype)

        #  check if dimensions are available, if not skip the flight
        if flight_i.acdimensions != None:
            
            # calculate the pairs with the flights that come after flight_i in the list, to avoid repeating pairs and comparing a flight with itself
            for flight_j  in flights[i + 1:]:
                
                # get dimensions of the flight, if not already done
                if flight_j.acdimensions == None:
                    flight_j._acdimensions = get_actype(flight_i.actype)
                
                # start performance timer
                time1 = perf_counter()

                # if (flight_i.min_fl > flight_j.max_fl + 10) or (flight_i.max_fl < flight_j.min_fl - 10):
                  #  continue

                # calculate several values related to proximity and occupancy
                occup, occup_vert, occup_horz, occup_overlap, start, finish,  prox_start, prox_finish, CRij_overlap, CRij_vertical, CRij_lateral ,\
                      Pz, ave_rel_speed, direction, py0, pair_flight_time, time_lat, time_vert, time_overlap = calc_values_ij(flight_i, flight_j, step = TIME_STEP, alt_max = ALT_MAX)

                # calculate global occupancies and py0
                total_flight_time += pair_flight_time 
                total_time_lat_vert += (time_lat + time_vert) * 2 
                total_time_lateral_pairs += time_lat * 2
                total_time_vertical_pairs += time_vert * 2
                total_time_overlap += (time_overlap * 2)
                
                total_py0 += py0 * pair_flight_time

                # if the pairs are proximate
                if occup != 0.0:
                    py0_old = calc_py0(flight_i, flight_j)
                    
                    # record results to save later on
                    # if True or CRij_lateral > 1 or CRij_vertical>1 or CRij_vertical <0 or Pz > 1 or py0 >= 1:
                        
                    track = RANDOM if (flight_i.ots == "0" and flight_j.ots == "0") else OTS if (flight_i.ots == "1" and flight_j.ots == "1") else MIX
    
                    pairs.loc[len(pairs)]=[TRAFFIC_TYPE[direction], TRACK[track], flight_i.id, flight_i.callsign, flight_i.elapsed_time_surveillance, flight_j.id, flight_j.callsign, flight_j.elapsed_time_surveillance, dt.fromtimestamp(start), dt.fromtimestamp(finish),
                        dt.fromtimestamp(prox_start),dt.fromtimestamp(prox_finish), ave_rel_speed[0], ave_rel_speed[1], ave_rel_speed[2],
                        py0, py0_old, Pz, time_overlap, time_lat, time_vert, occup, occup_vert, occup_horz, occup_overlap, CRij_overlap, CRij_vertical, CRij_lateral]
                                        
                    # get sum dimensions of both aircraft, not used
                    # dimensions = [ flight_i.acdimensions.length+flight_j.acdimensions.length, flight_i.acdimensions.wingspan+flight_j.acdimensions.wingspan, flight_i.acdimensions.height + flight_j.acdimensions.height]
                    
                    # calculate CRij
                    # CRij = calc_CRz(py0, dimensions=dimensions, Sx = 2*30, Ez = occupancy, speed=speeds)
                    
                    # lambda_z = max(flight_i.acdimensions.height, flight_j.acdimensions.height)
                    # lambda_x = max(flight_i.acdimensions.length, flight_j.acdimensions.length)
                    # lambda_y = max(flight_i.acdimensions.wingspan, flight_j.acdimensions.wingspan)

                    
                    # CR_overlap = CRij_overlap # * lambda_x / 30  
                    # CR_vertical = py0 * CRij_vertical # * lambda_x/ 30
                    #CR_lateral = CRij_lateral

                    sumCR_overlap  += CRij_overlap
                    sumCR_vertical += py0 * CRij_vertical
                    sumCR_lateral  += CRij_lateral * 2 * TIME_STEP

                else:
                    # print('No interaction:',ave_rel_speed)
                    pass
                
                time_spent += (perf_counter()-time1)

                if c % 100 == 0:
                    print ('\r',c,'/',combs,'   ',flight_i.callsign,' x ',flight_j.callsign, 'total time is ',round(time_spent,2),'seconds, average time/pair:',round(time_spent/c,3),'     iterations:',calc_values_ij.iterations,'     ', end='' )
                c+=1
        else:
            print("No dimensions for {}, actype is {}".format(flight_i.acid, flight_i.actype))
    
    # calculate average speed of pairs that interact
    try:
        ave_speeds = pairs[['dVx (Knots)','dVy (Knots)','dVz (Knots)']].mean()    
    except RuntimeError as error:
        print('Calc.py, line 334 - ',error)

    results.append(['Flight count',len(flights)])
    results.append(['Pair count',len(pairs)])
    
    results.append(['Time with vertical pairs (Sec)',total_time_vertical_pairs])
    results.append(['Time with with lateral pairs (Sec)',total_time_lateral_pairs])
    results.append(['Time with overlapping pairs (Sec)',total_time_overlap])
    
    results.append(['Mean absolute dVx', abs(ave_speeds.iloc[0])])
    results.append(['Mean absolute dVy', abs(ave_speeds.iloc[1])])
    results.append(['Mean absolute dVz', abs(ave_speeds.iloc[2])])    

    print ('\rTotal pairs:',c,' in ',round(time_spent,2),'seg. , average time/pair:',round(time_spent/c,3),'     ', end='')
   
    # check if the multiplication by TIME_STEP is correct
    total_CR_overlap = (2 * TIME_STEP * sumCR_overlap) / total_flight_time
    total_CR_vertical = (2 * TIME_STEP * sumCR_vertical) / total_flight_time
    total_CR_lateral = (sumCR_lateral) / total_flight_time

    results.append(['CR Overlap', total_CR_overlap])
    results.append(['CR Vertical', total_CR_vertical])
    results.append(['CR Lateral', total_CR_lateral])
    results.append(['Vertical occupancy',total_time_vertical_pairs/total_flight_time])
    results.append(['Lateral occupancy',total_time_lateral_pairs/total_flight_time])
    results.append(['Occupancy',total_time_lat_vert/total_flight_time])
    results.append(['Horizontal overlap',total_time_overlap/total_flight_time])
    results.append(['Py0',total_py0 / total_flight_time])
    # TODO add the mean kinetic term to the results.

    pairs.to_csv(outfile, index=False, sep=';')

    results = pd.DataFrame(results).rename({0:'Item',1:'Value'}, axis='columns')
    results.to_csv(results_filename,sep=',', decimal='.' , index=False)
    print(results)

    
if REDIRECT_TO_FILE:
    sys.stdout.close()