from geographiclib.geodesic import Geodesic
import time
from module.geo import distance_haversine, mA, distance_bearing

start_time = time.perf_counter()

for r in range(0,5000000):
    g = Geodesic.WGS84.Inverse(45.23, -33.0, 35.22, -17)
elapsed = time.perf_counter() - start_time
print(f"Main loop execution time: {elapsed:.6f} seconds")
print (g)

start_time = time.perf_counter()
for r in range(0,5000000):
    g = distance_bearing(45.23, -33.0, 35.22, -17)
elapsed = time.perf_counter() - start_time
print(f"2nd loop execution time: {elapsed:.6f} seconds")
print (g)