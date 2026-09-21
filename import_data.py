from module import *
from report import Report
from csv import DictReader
from os import path
import pickle
from flight import Flight, get_sub_field
from utils import save_flights, try_float, try_int, load_flights
from module.geo import xtrack_haversine, mod # x_track_fix, mod
from mwg import *
from datetime import datetime as dt
from dateutil.parser import parse

def import_flights(filename_csv: str = '', output_obj:str = "", output_res:str='', report_step = 10, interpolate : bool = True, filter = None, ANSP = None):
    
    """
    Import flights from data files, create the flight's list
    Can be adapted for any file that follows the format

    Args:
        file_name (str, optional): filename of th csv file to read.
        output (str, optional): filename of the output file to write to.
        report_step (int, optional): number of position reports to skip. Defaults to 10.

    Returns:
        dict: dictionary of objects of class Flight, key = unique flight id
    """

    # if no input filename is specified, the functions exits, returning None values
    if filename_csv == '':
        print('No input file specified. Exiting.')
        return None, None, None

    # determines the binary file name
    filename_obj = path.splitext(filename_csv)[0]+'.obj' if output_obj == "" else output_obj
    print("OBJ filename is ",filename_obj)
    
    # determines the text file name with the results.
    filename_res = path.splitext(filename_csv)[0]+'.summary.csv' if output_res == "" else output_res
    print("results filename will be ",filename_res)

    flights = None
    flights_second = None
    
    # if the binary file exists, load it
    if path.isfile(filename_obj):
        #load processed file from disk
        print ("Loading ",filename_obj)
        flights, flights_second = load_flights(filename=filename_obj)
        print ("Done.")

        if flights is not None and flights_second is None:
            print('Flights loaded, recreating flights per each second')
            flights_second = process_flights(flights, start=0 , finish=24*60*60)
            print('Done, saving again.')
            save_flights(flights = flights, flights_per_second=flights_second, filename=filename_obj)
            print('Done importing flights.')

    if flights is None:
        # the OBJ file does not exist, create it
        print("Reading and importing flight list ...")
        print(filename_csv, "\n")

        # create an empty flight list indexed by unique id
        flights = {}
 
        # read flight list
        with open(filename_csv, 'r',encoding="utf-8-sig", errors="replace") as file:
            # read the CSV list into a dictionary
            reader = DictReader(file, delimiter=",")
            # print(dict(list(flights_reader)[0]).keys())
            # skip first line, contains the header
            # next(flights_reader)

            # global counter variables
            counter = 0
            dupes = 0

            flight = None
            
            for line in reader:
                # for visual indication on progress
                if counter % 1000 == 0:
                    print("\r>> You have imported {} reports with {} dupes".format(counter, dupes), end='')
               
                flight_id = int(line['flight_id']) # unique id
                
                """
                if flight_id == 5846465:
                    pass
                """
                counter += 1

                if filter != None and len(filter)>0 and not (flight_id in filter):
                    continue

                # does the flight exist ?
                if (flight != None and flight.id != flight_id) or (flight == None):
                    flight = flights.get(flight_id)
                    
                    callsign = line['f170_target_id']  # flight's callsign   
                    addr = line['f080_target_addr']    # hex addr of the transponder
                    if flight == None:
                        # read flight plan information from the report
                        ots = line['ots'] # is the flight on OTS ?
                        equip10a = line['rad_nav_equipment']
                        equip10b = line['ssr_equipment']
                        other_info = line['otherinfo_text']
                        actype = line['aircraft_type_text']
                        field18 = get_sub_field(other_info)

                        # analyse FPL information
                        # check if the flight is pbcs
                        if len(field18)>0:
                            pbcs = "1" if "SUR" in field18 and "RSP180" in field18["SUR"] and "P2" in equip10a else "0"
                            # check if the flight is rnp4 or rnp10
                            try:
                                rnp4 = "1" if "L1" in field18[PBN][0] else "0"
                            except:
                                rnp4 = "0"

                            try:
                                rnp10 = "1" if "A1" in field18[PBN][0] else "0"
                            except:
                                rnp10 = 0

                        else:
                            pbcs = "0"
                            rnp4 = "0"
                            rnp10 = "0"

                        # create dictionary with the available info
                        info = {ID: flight_id, CALLSIGN: callsign, EQUIP10A: equip10a, EQUIP10B: equip10b, PBCS: pbcs,
                            RNP4: rnp4, RNP10: rnp10, OTS: ots, CODE: addr, MOPS:0, ACTYPE:actype }

                        # create the new flight
                        flight = Flight(info)
                        
                        # add to the list of flights
                        flights[flight_id] = flight

                    # Creates the flight's route profile.
                    # Does this only once per flight
                    if len(flight.profile) == 0:
                        try:
                            flight_profile_timestamps = list(map(lambda ts:parse(ts),line['fix_timestamps'].split(';')))
                            flight_profile_lats = line['fix_lats'].split(';')
                            flight_profile_longs = line['fix_lons'].split(';')        

                            # print(len(flight_profile_timestamps))                 
                        
                            if len(flight_profile_timestamps) == len(flight_profile_lats) == len(flight_profile_longs):
                                flight.profile = list(map(lambda lat, lon, timestamp : Report({LAT:lat, LONG:lon, TIMESTAMP:timestamp, FL:None}),flight_profile_lats,flight_profile_longs,flight_profile_timestamps))
                        
                            flight.sort_profile()
                        
                        except Exception as e:
                            print(f'\n{callsign} has no fight profile, or flight profile is inconsistent,   ', e)
                       
                    # Add the callsign if it was missed on a previous report, the correlation is established by flight_id
                    if flight.callsign == "" and callsign != "":
                        flight.callsign = callsign
                    # Add the hex addr if it was missed on a previous report, the correlation is established by flight_id
                    if flight.code == "" and addr != "":
                        flight.code = addr

                try:
                    timestamp = line['f073_timeof_rx_pos']
                    timestamp_bin = parse(timestamp)
                except Exception as e:
                    timestamp_bin = None                

                """    
                try:
                    seconds = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    # seconds from midnight
                    
                except:
                    seconds = 0
                """

                # position report data
                lt = line['lat'].replace(',','.')
                try: 
                    lat = float(lt) # * (-1 if ANSP == 4 else 1) 
                except:
                    lat = None

                lg = line['lon'].replace(',','.')
                try:
                    lon = float(lg) 
                except:
                    lon = None

                f = line['f145_fl']
                try:
                    fl = float(f) if (ANSP != CANADA and ANSP != PORTUGAL) else float(f)/100
                    
                except:    
                    fl = None

                # get ground track from the report
                try:
                    b = line['f160_gndvec_trk_angle']
                    # make sure that 0 <= bearing < 360.0
                    bearing = mod(float(b), 360)
                except:
                    bearing = None
                
                # get ground speed from the report, NM/s
                # check the diferences in speed
                gs = line['f160_gndvec_gnd_speed']
                try:
                    ground_speed = float(gs)*3600 if ANSP != CANADA else float(gs)
                except:
                    ground_speed = None
                
                # receiving station SIC
                sic = try_int(line['f010_sic']) if 'f010_sic' in line else 0
                # receiving station SAC
                sac = try_int(line['f010_sac']) if 'f010_sac' in line else 0
                # mops version                
                mops = try_int(line['f210_mops_ver']) if 'f210_mops_ver' in line else 0
                
                # check the MOPS, to see if there is any change to 2
                flight.mops = mops if mops == 2 else flight.mops

                # add report data to the flight, if the report data is valid
                # needs to have a latitude, longitude, flight level and timestamp
                if lat is not None and lon is not None and fl is not None and timestamp is not None:

                    # check if it faster with hashing
                    resume = (timestamp, lat, lon, f)

                    # check if the report is a duplicate, if so ignores it.
                    if resume not in flight.duplicates:
                        # assume default value None for CTE
                        cte = None

                        # assume default values por projected latitude and longitude
                        # proj_lat = None
                        # proj_lon = None

                        # get flight profile
                        profile = flight.profile
                        
                        # if we have at least two points
                        if len(profile)>1:
                            # is the current time within the recorded profile time span ?
                            if timestamp_bin>=profile[0].timestamp_bin and timestamp_bin<=profile[-1].timestamp_bin:
                                for p in range(0,len(profile)-1):
                                    p1 : Report = profile[p]
                                    p2 : Report = profile[p+1]
                                    
                                    # determine the flight segment that might pertain to this flight
                                    if timestamp_bin >= p1.timestamp_bin and timestamp_bin< p2.timestamp_bin:
                                        # calculate the CTE for this position report
                                        # xdist, proj_lat, proj_lon, adist = x_track_fix(p1.lat, p1.long, p2.lat, p2.long, lat, lon)
                                        xtrackdistance, proj_lat, proj_lon, along_distance = xtrack_haversine(p1.lat, p1.long, p2.lat, p2.long, lat, lon)
                                        # calculate the slop value in NM
                                        cte = round(xtrackdistance / 1852, ndigits=3)
                                        break
                    

                        # creates the report
                        report = Report({LAT: lat, LONG: lon, FL: fl, TIMESTAMP: timestamp, SECONDS: 0, GT: bearing, GS:ground_speed,
                                    SIC:sic, SAC:sac, CODE: addr, CTE:cte, PROJ_LAT:None, PROJ_LON:None})
                        # flight.add_surv_rep(line)
                        flight.surveillance.append(report)
                        flight.set_duplicate(resume)
                    
                    else:
                        dupes += 1               
                
        print(f"\r>> You have imported {counter} reports with {dupes} dupes")
       
        print("Done")
        max = len(flights)
        print('Nº voos : {}'.format(max))
        
        print("Sorting reports, calculating interpolations and cleaning up duplicate list.")
        c = 1
        
        for id in flights:
            flight : Flight = flights[id]
            # TODO calculate the CTE here, after sorting the flight profile and reports
            
            # clears the flight's duplicates list
            flight.duplicates = {}
            flight.sort_reports()
            flight.set_min_max_fl()
            
            if interpolate:
                # reduces the number of reports to interpolate from
                flight.decimate_surveillance(step = report_step)            
                flight.interpolate_all()

            print ('\r',flight.callsign, " ",c,"/",max, end='  ')

            # interpolated = list(flight.interpolated.keys())
            # first = dt.fromtimestamp(interpolated[0]).strftime('%Y-%m-%d %H:%M:%S')
            # last = dt.fromtimestamp(interpolated[-1]).strftime('%Y-%m-%d %H:%M:%S')
            # elapsed = (dt.fromtimestamp(interpolated[-1]) - dt.fromtimestamp(interpolated[0])).total_seconds()
            # print(flight.callsign, first, last, len(interpolated), elapsed)
            # print(flight.surveillance[0].timestamp_bin)
            # print(flight.surveillance[-1].timestamp_bin,'\n')
            # print(flight.profile[0].timestamp_bin)
            # print(flight.profile[-1].timestamp_bin,'\n')

            c += 1
            
        print("Completed sorting reports, calculating interpolations and cleaning up duplicate list.\nCreating dict of flights at each second")
        
        flights_second = process_flights(flights)

        print("Done.\nSaving to file ", filename_obj)
        save_flights(flights = flights, flights_per_second = flights_second, filename=filename_obj)
        print("Saving to file ", filename_obj," complete.")        
     
    return flights, flights_second, filename_res

def process_flights(flights: dict, start: int = 0, finish: int = 2147483647): 

    """
    Clusters flightids per timestamp
    
    Args:
         flights : flight list
         start   : first timestamp to process, UNIX timestamp in seconds, default 0 (1970-01-01 00:00:00)
         finish  : last timestamp to process, UNIX timestamp in seconds, default 2147483647 (2038-01-19 03:14:07)

    Returns:
        dictionary with processed data  { timestamp : [list of flight ids with an interpolated report at that timestamp]}
    """

    print('Getting list of flights at timestamp !')
    flights_second = {}
    ## fl = list(flights.values())

    def has_interpolated(f:Flight)-> bool:
        return f is not None and f.interpolated is not None and len(f.interpolated.keys())>0
    
    usable = list(filter(has_interpolated, flights.values()))

    # t1 = fl[0]
    # times = list(t1.interpolated.keys())
    # m = min(times)

    # m = list(map(lambda f:list(f.interpolated.keys()), fl))
    
    try:
        start_second  = min(list(map(lambda f: min(list(f.interpolated.keys())), usable)))
        finish_second = max(list(map(lambda f: min(list(f.interpolated.keys())), usable)))
    
    except:
        start_second = 0
        finish_second = 0

    print(start_second, finish_second)

    for i in range(start_second, finish_second+1):
        flights_second[i] = list(map(lambda f:f.id, list(filter(lambda p: i in p.interpolated, usable))))
        if (finish_second - i) % 1000 == 0:
            print('\r',i,':',finish_second,'  ',len(flights_second[i]),' voos',end='  ')
    print('\r',finish_second,':',finish_second,'  ',len(flights_second[finish_second]),' voos \n\nDone !')
    return flights_second
