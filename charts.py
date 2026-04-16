from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import time
from flight import Flight
print('import numpy, charts')
import numpy as np
print('Finished charts import')

def start_chart_display() -> Basemap:
    """
    # setup lambert conformal basemap.
    # lat_1 is first standard parallel.
    # lat_2 is second standard parallel (defaults to lat_1).
    # lon_0, lat_0 is central point.
    # rsphere=(6378137.00,6356752.3142) specifies WGS84 ellipsoid
    # area_thresh=1000 means don't plot coastline features less than 1000 km^2 in area.
    """
    plt.figure(figsize=(16, 16))
    m: Basemap = Basemap(width=16000000, height=9000000, rsphere=(6378137.00, 6356752.3142), resolution='l',
        projection='lcc', lat_1=40., lat_2=70, lat_0=66.0, lon_0=-18.0, llcrnrlat=55, llcrnrlon=-50.0, urcrnrlat=75.0, urcrnrlon=12.0)
    m.drawcoastlines(linewidth=0.3)
    m.fillcontinents(color='#cccccc', lake_color='lightskyblue')
    m.drawparallels(np.arange(40., 80., 1.), linewidth=0.5, labels = [False,True,True,True])
    m.drawmeridians(np.arange(-60., 10., 1.), linewidth=0.5, labels = [False,False,False, True])
    m.drawmapboundary(fill_color='lightskyblue')
    m.drawlsmask(land_color="gray")

    # show BIRD Oceanic FIR on the map
    m.readshapefile('./shp/bird', 'bird', linewidth=1, color="black")
    m.readshapefile('../shp/nuuk', 'nuuk', linewidth=1, color="black")
    # m.readshapefile('../shp/nuuk_del', 'nuuk_del', linewidth=1, color="red")
    
    return m
    # plt.show()        


def do_chart_display(flights: dict = None, ts: int = 0):
    """
    # setup lambert conformal basemap.
    # lat_1 is first standard parallel.
    # lat_2 is second standard parallel (defaults to lat_1).
    # lon_0, lat_0 is central point.
    # rsphere=(6378137.00,6356752.3142) specifies WGS84 ellipsoid
    # area_thresh=1000 means don't plot coastline features less than 1000 km^2 in area.
    """
    plt.figure(figsize=(16, 16))
    m: Basemap = Basemap(width=16000000, height=9000000, rsphere=(6378137.00, 6356752.3142), resolution='l',
        projection='lcc', lat_1=40., lat_2=70, lat_0=66.0, lon_0=-18.0, llcrnrlat=55, llcrnrlon=-50.0, urcrnrlat=75.0, urcrnrlon=12.0)
    m.drawcoastlines(linewidth=0.3)
    m.fillcontinents(color='#cccccc', lake_color='lightskyblue')
    # m.drawparallels(np.arange(-10., 55., 1.), linewidth=0.5)
    # m.drawmeridians(np.arange(-50., 10., 1.), linewidth=0.5)
    m.drawmapboundary(fill_color='lightskyblue')
    m.drawlsmask(land_color="gray")

    # show BIRD Oceanic FIR on the map
    m.readshapefile('../shp/bird', 'bird', linewidth=1, color="black")
    m.readshapefile('../shp/nuuk', 'nuuk', linewidth=1, color="black")
    m.readshapefile('../shp/nuuk_del', 'nuuk_del', linewidth=1, color="red")    
    
    if flights:
        for f in flights.values():
            # draw interpolated reports
            if ts != 0 and f.interpolated and ts in f.interpolated:
                point = f.interpolated[ts]
                lat = point[0]
                lon = point[1]
                alt = point[2]
                
                if alt >0:
                    # plot the time vector
                    ys = [point[0], point[5]]
                    xs = [point[1], point[6]]
                    m.plot(latlon=True, x=xs, y=ys, linewidth=0.6, color="black")

                    #lats = list(map(lambda a: a[0], v))
                    #longs = list(map(lambda a: a[1], v))
                    # m.plot(latlon=True, x=list(longs), y=list(lats), linewidth=3, color="red")
            
                    # lats = list(map(lambda a: a.lat, f.surveillance))
                    # longs = list(map(lambda a: a.long, f.surveillance))
                    # m.scatter(latlon=True, x=list(longs), y=list(lats), s=12, color="black")
                   
                    m.scatter(latlon = True, x=lon, y=lat, s = 10, color = "black")
                    # m.plot(latlon=True, x=list(longs), y=list(lats), linewidth=0.5, color="dimgray")

                    x, y = m(point[1], point[0] + 0.05)
                    plt.text(x, y, s=f.acid + "/" + str(round(alt, 0)), fontsize=7)

            """
            lats = list(map(lambda a: a.lat, f.surveillance))
            longs = list(map(lambda a: a.long, f.surveillance))
            # m.plot(latlon=True, x=list(longs), y=list(lats), linewidth=0.1, color="black")
            m.scatter(latlon=True, x=list(longs), y=list(lats), s=3, color="black")
            """

    plt.title("Occupancy in Reykjavik at " + time.strftime('%H:%M:%S', time.gmtime(ts)))
    plt.tight_layout()

def plot_flight(f:Flight):
    """
    Plots altitudes along the timestamps (in seconds) for a flight

    Args:
        f (Flight): Flight to plot the information
    """
    altitudes = list(map(lambda a : a[2], list(f.interpolated.values())))
    plt.plot(list(f.interpolated.keys()), altitudes)
    plt.show

def plot_flights(flight_list:dict, start = -1, finish = -1, m:Basemap = None):
    """
    Plots interpolated position reports 

    Args:
        f (Flight): Flight to plot the information
    """
    

    if m is None:

        m = start_chart_display()

    """    
    m : Basemap = Basemap(width=16000000, height=9000000, rsphere=(6378137.00, 6356752.3142), resolution='l',
        projection='lcc', lat_1=40., lat_2=70, lat_0=66.0, lon_0=-18.0, llcrnrlat=55, llcrnrlon=-50.0, urcrnrlat=75.0, urcrnrlon=12.0)
    m.drawcoastlines(linewidth=0.3)
    m.fillcontinents(color='#cccccc', lake_color='lightskyblue')
    # m.drawparallels(np.arange(-10., 55., 1.), linewidth=0.5)
    # m.drawmeridians(np.arange(-50., 10., 1.), linewidth=0.5)
    m.drawmapboundary(fill_color='lightskyblue')
    m.drawlsmask(land_color="gray")

    # show BIRD Oceanic FIR on the map
    m.readshapefile('../shp/bird', 'bird', linewidth=1, color="black")
    m.readshapefile('../shp/nuuk', 'nuuk', linewidth=1, color="black")
    m.readshapefile('../shp/nuuk_del', 'nuuk_del', linewidth=1, color="red")
    """

    # plot the flights
    for key in flight_list:
        lats = []
        lons = []
        for s in flight_list[key].interpolated:
            if start == -1 or start<=s<=finish:
                lats.append(flight_list[key].interpolated[s][0])
                lons.append(flight_list[key].interpolated[s][1])
        # lats = list(map(lambda a : a[0], list(flight_list[key].interpolated.values())))
        # lons = list(map(lambda a : a[1], list(flight_list[key].interpolated.values())))
        lons, lats = m(lons,lats)
        m.scatter(lons, lats, marker='o', c= np.random.rand(3,), s=2)
    
    plt.get_current_fig_manager().full_screen_toggle()
    plt.show()
    

def plot_flight_interpolated(f:Flight, start :int = -1, finish:int = -1, m : Basemap = None):
    """
    Plots interpolated position reports 

    Args:
        f (Flight): Flight to plot the information
    """
    if m is None:
        m = start_chart_display()

    reports = { second : report for second, report in f.interpolated.items() if start == -1 or start <= second <= finish}

    lats = list(map(lambda a : a[0], list(reports.values())))
    lons = list(map(lambda a : a[1], list(reports.values())))
    
    lons, lats = m(lons,lats)
    m.scatter(lons, lats, marker='o', color= np.random.rand(3,), s=2)
    
    # plot the 1st point
    m.scatter(lons[0],lats[0], latlon = 0, marker = 'X', s=5, color = 'red')
    
    plt.text(lons[0],lats[0],'{}/{}/{}'.format(f.acid,f.id,f.surveillance[0].timestamp_bin))

    return m
    