import pickle
from flight import Flight
from pandas import DataFrame, read_csv, set_option
from datetime import datetime as dt
from geographiclib.geodesic import Geodesic
import numpy as np

FILENAME = "c:\\Data\\Canada_TBCRM_Data.obj" 

try:
    with open(FILENAME, 'rb') as file:
        flights = pickle.load(file)
        try:
            flights_second = pickle.load(file)
        except:
            flights_second = None
except Exception as error:
        print(error)

print(flights)
        
pairs = read_csv('c:\\Data\\Canada_TBCRM_Data.pairs.csv',delimiter=';')
pair = pairs.loc[733].to_dict()

f1_id = pair['F1_ID']
f2_id = pair['F2_ID']
start = pair['INTER_START']
finish = pair['INTER_FINISH']

f1 = flights[f1_id]
f2 = flights[f2_id]

f1_lats = [f1.interpolated[t][0] for t in f1.interpolated if t>= start and t<= finish]
f1_lons = [f1.interpolated[t][1] for t in f1.interpolated if t>= start and t<= finish]

f2_lats = [f2.interpolated[t][0] for t in f2.interpolated if t>= start and t<= finish]
f2_lons = [f2.interpolated[t][1] for t in f2.interpolated if t>= start and t<= finish]

gander_fir = read_csv(r'..\\gander.csv',delimiter=';')

from mpl_toolkits.basemap import Basemap
from matplotlib import pyplot as plt

lats = [63.5,58.5,58.5,63.5]
lons = [-55.6666666666666667,-50,-43,-39]

plt.figure(figsize=(10,10))
# criar a projeção conforme conica de lambert
#m = Basemap(projection = 'merc', resolution='i',
 #           llcrnrlat=40, llcrnrlon=-65, urcrnrlat=70, urcrnrlon=-28, lat_ts = 40)
m = Basemap(projection = 'lcc',rsphere=(6378137.00, 6356752.3142), resolution='l',
            llcrnrlat=40, llcrnrlon=-55, urcrnrlat=69, urcrnrlon=-28, lat_1 = 17, lat_2 = 70, lat_0=55, lon_0=-30)
# desenhar os contornos da FIR
m.drawcoastlines()
m.plot(gander_fir['Long'].to_list(), gander_fir['Lat'].to_list(), latlon = True)
m.plot(lons, lats, latlon = True)

result = Geodesic.WGS84.Inverse(lat1 = f1_lats[0], lon1 = f1_lons[0], lat2 = f2_lats[0], lon2 = f2_lons[0])
distance = round(result['s12']/1852,2)

m.plot(f1_lons,f1_lats,latlon = True, label = str(distance) )
m.plot(f2_lons,f2_lats,latlon = True)

meridians = np.arange(10.,351.,20.)
m.drawmeridians(meridians,labels=[True,False,False,True])

plt.title(str(distance))
plt.show()