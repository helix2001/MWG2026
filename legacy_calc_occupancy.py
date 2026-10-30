    

from module import *
from flight import *

def calc_occupancy_old(dataset, flights : dict, reference: int = REFERENCE_TIMESTAMP, duration: int = REFERENCE_SPAN, output:str = "", step = 1) -> dict:
    """ 
    Calculates occupancy using the old method, all flights.
    Calls the method Flight.check_proximity to determine if the flights are proximate.
    Args:
        dataset: dictionary with processed data in the format { timestamp : [list of flights with an interpolated report at that timestamp]}
        flights: dictionary of flights
        reference: start timestamp, in seconds from midnight
        duration: span, in seconds
        step: interval, in seconds, between consecutive calculations
        output: filename to hold the calculation results
    """
    # dictionary to hold the ocuppancy values
    total_ocuppancy = {}

    # list to hold total proximate pairs
    proximate = []
    
    flight_list = flights.values()

    for second in range(reference, reference+duration, step  ):
        # checks if there is interpolated data for the required second
        if second in dataset:
            # gets the list of flights with interpolated data at the required timestamp
            fl = dataset[second]
            
            # total flight count at the required timestamp
            flight_count = len(fl)

            # filter to obtain the count of ots flights
            flights_ots = list(filter(lambda a: a.id in fl and a.ots =="1" , flight_list))
            
            ots_count = len(flights_ots)

            # get random_flights_count
            random_count = flight_count - ots_count

            print("Occupancy, Flights of interest-", flight_count, " at timestamp ", second)
            
            # values for the occupancy at this timestamp
            ocuppancy = {
                VERTICAL : {
                    SAMEDIR: { OO:0.0, RR:0.0, OR:0.0},
                    OPPOSITE:{ OO:0.0, RR:0.0, OR:0.0} 
                }
                 ,
                LATERAL : {
                    SAMEDIR: { OO:0.0, RR:0.0, OR:0.0},
                    OPPOSITE:{ OO:0.0, RR:0.0, OR:0.0} 
                }
            }

            unique_flights = { VERTICAL: [], LATERAL: [] }
            proximity_pairs = { VERTICAL: [], LATERAL: [] }

            for i in range(0, flight_count - 1):
                f1: Flight = flights[fl[i]]
                for j in range(1, flight_count):
                    f2 = flights[fl[j]]
                    # checks if the flights are proximate at this timestamp
                    vertical, lateral, track, direction, overlap = f1.check_proximity(other=f2, second=second)
                    pair = [f1.callsign, f2.callsign, track, direction]

                    # lateral occupancy
                    if lateral:
                        proximate.append(f1.id)
                        proximate.append(f2.id)
                        # saves the list of unique flights that have lateral proximate flights
                        # used to create a filtered dataset for testing
                        if f1.callsign not in unique_flights[LATERAL]:
                            unique_flights[LATERAL].append(f1.callsign)
                        if f2.callsign not in unique_flights[LATERAL]:
                            unique_flights[LATERAL].append(f2.callsign)
                        
                        # increase the number of proximates pairs for lateral
                        proximity_pairs[LATERAL].append(pair)

                    # vertical occupancy
                    if vertical:
                        proximate.append(f1.id)
                        proximate.append(f2.id)
                        # saves the list of unique flights that have vertical proximate flights
                        # used to create a filtered dataset for testing
                        if f1.callsign not in unique_flights[VERTICAL]:
                            unique_flights[VERTICAL].append(f1.callsign)
                        if f2.callsign not in unique_flights[VERTICAL]:
                            unique_flights[VERTICAL].append(f2.callsign)
                        # increase the number of proximates pairs for vertical
                        proximity_pairs[VERTICAL].append([f1.callsign, f2.callsign, track, direction])

            # filters the vertical proximity list to get the counts in the various categories
            # RANDOM, OTS or MIXED
            # OPPOSITE or SAMEDIR
            vertical_random_samedir = list(filter(lambda a:a[2] == RANDOM and a[3] == SAMEDIR, proximity_pairs[VERTICAL]))
            vertical_ots_samedir = list(filter(lambda a:a[2] == OTS and a[3] == SAMEDIR, proximity_pairs[VERTICAL]))
            vertical_mix_samedir = list(filter(lambda a:a[2] == MIX and a[3] == SAMEDIR, proximity_pairs[VERTICAL]))
            vertical_random_opposite = list(filter(lambda a:a[2] == RANDOM and a[3] == OPPOSITE, proximity_pairs[VERTICAL]))
            vertical_ots_opposite = list(filter(lambda a:a[2] == OTS and a[3] == OPPOSITE, proximity_pairs[VERTICAL]))
            vertical_mix_opposite = list(filter(lambda a:a[2] == MIX and a[3] == OPPOSITE, proximity_pairs[VERTICAL]))

            # filters the lateral proximity list to get the counts in the various categories
            # RANDOM, OTS or MIXED
            # OPPOSITE or SAMEDIR
            lateral_random_samedir = list(filter(lambda a:a[2] == RANDOM and a[3] == SAMEDIR, proximity_pairs[LATERAL]))
            lateral_ots_samedir = list(filter(lambda a:a[2] == OTS and a[3] == SAMEDIR, proximity_pairs[LATERAL]))
            lateral_mix_samedir = list(filter(lambda a:a[2] == MIX and a[3] == SAMEDIR, proximity_pairs[LATERAL]))
            lateral_random_opposite = list(filter(lambda a:a[2] == RANDOM and a[3] == OPPOSITE, proximity_pairs[LATERAL]))
            lateral_ots_opposite = list(filter(lambda a:a[2] == OTS and a[3] == OPPOSITE, proximity_pairs[LATERAL]))
            lateral_mix_opposite = list(filter(lambda a:a[2] == MIX and a[3] == OPPOSITE, proximity_pairs[LATERAL]))

            # calculate vertical occupancies
            
            ocuppancy[VERTICAL][SAMEDIR][RR] = (2 * len(vertical_random_samedir) + len(vertical_mix_samedir)) / random_count if random_count > 0 else NO_OCCUP
            ocuppancy[VERTICAL][SAMEDIR][OO] = (2 * len(vertical_ots_samedir) + len(vertical_random_samedir))/ ots_count if ots_count > 0 else NO_OCCUP
            ocuppancy[VERTICAL][SAMEDIR][OR] = 2 * (len(vertical_random_samedir) + len(vertical_ots_samedir) + len(vertical_mix_samedir)) / flight_count if flight_count > 0 else NO_OCCUP

            ocuppancy[VERTICAL][OPPOSITE][RR] = (2 * len(vertical_random_opposite) + len(vertical_mix_opposite)) / random_count if random_count > 0 else NO_OCCUP
            ocuppancy[VERTICAL][OPPOSITE][OO] = (2 * len(vertical_ots_opposite) + len(vertical_random_opposite)) / ots_count if ots_count > 0 else NO_OCCUP
            ocuppancy[VERTICAL][OPPOSITE][OR] = 2 * (len(vertical_random_opposite) + len(vertical_ots_opposite) + len(vertical_mix_opposite)) / flight_count if flight_count > 0 else NO_OCCUP

            # calculate lateral occupancies

            ocuppancy[LATERAL][SAMEDIR][RR] = (2 * len(lateral_random_samedir) + len(lateral_mix_samedir)) / random_count if random_count > 0 else NO_OCCUP
            ocuppancy[LATERAL][SAMEDIR][OO] = (2 * len(lateral_ots_samedir) + len(lateral_random_samedir))/ ots_count if ots_count > 0 else NO_OCCUP
            ocuppancy[LATERAL][SAMEDIR][OR] = 2 * (len(lateral_random_samedir) + len(lateral_ots_samedir) + len(lateral_mix_samedir)) / flight_count if flight_count > 0 else NO_OCCUP

            ocuppancy[LATERAL][OPPOSITE][RR] = (2 * len(lateral_random_opposite) + len(lateral_mix_opposite)) / random_count if random_count > 0 else NO_OCCUP
            ocuppancy[LATERAL][OPPOSITE][OO] = (2 * len(lateral_ots_opposite) + len(lateral_random_opposite)) / ots_count if ots_count > 0 else NO_OCCUP
            ocuppancy[LATERAL][OPPOSITE][OR] = 2 * (len(lateral_random_opposite) + len(lateral_ots_opposite) + len(lateral_mix_opposite)) / flight_count if flight_count > 0 else NO_OCCUP

            total_ocuppancy[second] = [flight_count, proximity_pairs, unique_flights, ocuppancy, ots_count, random_count,
                len(vertical_ots_samedir),len(vertical_random_samedir), len(vertical_mix_samedir),
                len(vertical_ots_opposite),len(vertical_random_opposite), len(vertical_mix_opposite),
                len(lateral_ots_samedir),len(lateral_random_samedir), len(lateral_mix_samedir),
                len(lateral_ots_opposite),len(lateral_random_opposite), len(lateral_mix_opposite)]

    print(f'Finished calculationg occupancy!')

    list_proximate = list(dict.fromkeys(proximate))
    print(proximate)
    print(list_proximate)

    # creates a dictionary with occupancy values, keys are the timestamps, in seconds from midnight
    occupancy_csv = {}
    for i in total_ocuppancy:
        values = total_ocuppancy[i]
        to = values[3]
        occupancy_csv[i] = [i, values[0],values[4],values[5],
        to[VERTICAL][SAMEDIR][OO], values[6], to[VERTICAL][SAMEDIR][RR], values[7], to[VERTICAL][SAMEDIR][OR], values[8],
        to[VERTICAL][OPPOSITE][OO], values[9], to[VERTICAL][OPPOSITE][RR], values[10], to[VERTICAL][OPPOSITE][OR], values[11],
        to[LATERAL][SAMEDIR][OO], values[12], to[LATERAL][SAMEDIR][RR], values[13], to[LATERAL][SAMEDIR][OR], values[14],
        to[LATERAL][OPPOSITE][OO], values[15], to[LATERAL][OPPOSITE][RR], values[16], to[LATERAL][OPPOSITE][OR], values[17]] 
       

    # write the occupancy to a file
    if output != "":
        columns = ["Second","TotalFlights","OtsFlights","RandomFlights",
                   "VertOccSameOTS", "Count", "VertOccSameRan","Count","VertOccSameCombined","Count",
                   "VertOccOppOTS","Count", "VertOccOppRan","Count", "VertOccOppCombined","Count", 
                   "LatOccSameOTS","Count", "LatOccSameRan","Count", "LatOccSameCombined","Count", 
                   "LatOccOppOTS","Count", "LatOccOppRan","Count", "LatOccOppCombined","Count" ]
        
        with open(output+'.csv', mode='w', newline='') as ficheiro_csv:
            export = csv.writer(ficheiro_csv, delimiter=';')
            export.writerow(columns)
            export.writerows(list(occupancy_csv.values()))

    # returns the full dictionary
    return total_ocuppancy
