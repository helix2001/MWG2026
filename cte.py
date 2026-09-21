import import_data
from functools import reduce
from pandas import read_csv, DataFrame
from numpy import histogram, arange, ceil, sum, linspace, squeeze, array
import matplotlib.pyplot as plt
import scipy.stats as sps
from statsmodels.distributions.empirical_distribution import ECDF
import numpy as np

# define constants to identify the columns of the flight data
ID= 0
AIRLINE = 1 
CALLSIGN = 2
ACTYPE = 3
CTE = 4
SLOPS = 5
S0  = 6
S1  = 7
S2  = 8
SLOP = 9

def main():
    flight_data = []
    flight_slops = []
    ctes = []
    errors = []

    per_airline = {}
    summary = []

    per_airline_ctes = {}

    data = import_data.import_flights(filename_csv="lppo_2025.csv", interpolate = False)
    for id in data[0]:
        # get the flight id
        flight = data[0][id]

        try:
             if flight.max_fl < 28800 or flight.min_fl > 41200:
                 # print(f'\n{flight.callsign} is outside of RVSM levels')
                 errors.append(flight.callsign)
                 continue
        
        except Exception as e:
            #print(f'\n{flight.callsign} has no max_fl or min_fl, or they are inconsistent,   ', e)
            errors.append(flight.callsign)
            continue
    
        # add the ctes to the global list of ctes
        ctes.extend(flight.ctes)
        
        # get the SLOP from the ctes
        flight_slop = list(filter(lambda x: x!=3,
            (map(lambda x: 0 if -0.5< x <0.5 else 1 if 0.5 <=x <1.5 else 2 if 1.5 <=x <2.5 else 3, flight.ctes))))
        
        slop0   = len(list(filter(lambda x: x==0, flight_slop)))
        slop1   = len(list(filter(lambda x: x==1, flight_slop)))
        slop2   = len(list(filter(lambda x: x==2, flight_slop)))
        
        
        # add the flight slop to the global list of flight slops
        flight_slops.extend(flight_slop)

        # determine the most common slop for the flight
        maxi = max(slop0, slop1, slop2)
        if maxi == slop0:
            fslop = 0
        elif maxi == slop1:
            fslop = 1
        else:            
            fslop = 2


        airline = flight.callsign[0:3]
        # add the flight data to the global list of flight data
        flight_data.append([flight.id, airline, flight.callsign, flight.actype,flight.ctes, fslop,flight_slop,slop0,slop1
                            ,slop2])
        
        # determine the ctes per airline
        try:
            per_airline_ctes.get(airline).extend(flight.ctes)        
        except Exception as e:
            per_airline_ctes[airline] = flight.ctes

        # if airline == 'IBE':
          #  pass

        try:
            per_airline.get(airline).extend(flight_slop)        
        except Exception as e:
            per_airline[airline] = flight_slop

    for airline in per_airline:
        slop0   = len(list(filter(lambda x: x==0, per_airline[airline])))
        slop1   = len(list(filter(lambda x: x==1, per_airline[airline])))
        slop2   = len(list(filter(lambda x: x==2, per_airline[airline])))
        total_count = slop0 + slop1 + slop2
        maxi = max(slop0, slop1, slop2)
        if maxi == slop0:
            slop = 0
        elif maxi == slop1:
            slop = 1
        else:            
            slop = 2

        summary.append([airline,slop0, slop1, slop2, total_count, slop])
        

    summary.sort(key=lambda x: x[4], reverse=True)

    df_summary = DataFrame(summary[0:25], columns=['Airline', 'Slop0', 'Slop1', 'Slop2', 'Total', 'Slop'])
    df_summary.to_csv('summary.csv', index=False)



    print('ERRORS:', len(errors))
    print('CTES:', len(ctes))
    print('FLIGHT SLOPS:', len(flight_slops))
    print('FLIGHTS:', len(flight_data))

    SLOP0 = list(filter(lambda x: x[5]==0, flight_data))
    SLOP1 = list(filter(lambda x: x[5]==1, flight_data))
    SLOP2 = list(filter(lambda x: x[5]==2, flight_data))

    print('SLOP0:{}, SLOP1:{}, SLOP2:{}'.format(len(SLOP0), len(SLOP1), len(SLOP2)))

    # start plotting the histogram of the ctes
    print('-----------------------\nCreating histogram')

    # define the number of bins for the histogram
    NUM_BINS = 1000
    # definition of an average wingspan value
    WINGSPAN = 0.030

    values, bins, patches = plt.hist(x=ctes, bins=NUM_BINS)
    maxvalue = values.max()
    plt.ylim(top = maxvalue + 10000)
    # plt.xlabel('CTE')
    # plt.ylabel('Absolute count')
    # plt.title('CTE in LPPO, 2025, {} flights, {} reports'.format(len(flight_data), len(ctes)))
    plt.show()
    plt.clf()

    res = sps.relfreq(ctes, numbins=3)
    x = res.lowerlimit + linspace(0, res.binsize*res.frequency.size, res.frequency.size)
    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim([0,2])
    ax.bar([0,1,2], res.frequency, width = 0.5) #res.binsize)
    # ax.set_title('Relative frequency histogram, 2025, {} flights, {} reports'.format(len(flight_data), len(ctes)))
    ax.set_xlim([x.min(), x.max()])
    plt.show()


    df_data = np.array(ctes, dtype=float)  # dtype is optional

    # df_data = DataFrame.to_numpy(ctes)
    ecdf = ECDF(df_data)
    min_cte = df_data.min()
    max_cte = df_data.max()

    print(min_cte, ' ', max_cte)
    count = int((max_cte-min_cte) / 0.001)

    plt.clf()
    plt.plot(ecdf.x, ecdf.y)
    plt.show()
    print('Create X vector {}'.format(count))
    steps = linspace(min_cte,max_cte,count)
    # print(steps)

    steps = zip(steps,steps[1:])

    npa = array(list(steps))

    steps = zip(npa,npa[1:])
    print('Calculating py0same')
    py0same = list(map(lambda x:(ecdf(x[1]+WINGSPAN)-ecdf(x[0]-WINGSPAN)) * (ecdf(x[1])-ecdf(x[0])) , npa))
    print('Calculating py0opposite')
    py0opposite = list(map(lambda x:(ecdf((-1*x[1])+WINGSPAN)-ecdf((-1*x[0])-WINGSPAN)) * (ecdf(x[1])-ecdf(x[0])) , npa))

    print('Summing py0same')
    print(sum(py0same))
    print('Summing py0opposite')
    print(sum(py0opposite))


    # Plotting a basic histogram    
    ctes = per_airline_ctes.get('AEA')
    plt.hist(ctes, bins=1000, color='skyblue', edgecolor='skyblue')
     # Adding labels and title
    plt.xlabel('SLOP')
    plt.ylabel('Frequency')
    # plt.title('CTE for {} in 2025'.format('TFL')) 
    # Display the plot
    plt.show()

    
    print('Done')

       
if __name__ == "__main__":
    main()