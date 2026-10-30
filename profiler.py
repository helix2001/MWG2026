from geographiclib.geodesic import Geodesic
import time
from module.geo import inverse_haversine

print("Starting wgs84 loop...")
start_time = time.perf_counter()
for r in range(0,5000000):
    g = Geodesic.WGS84.Inverse(45.23, -33.0, 35.22, -17)
elapsed = time.perf_counter() - start_time
print(f"WGS84 loop execution time: {elapsed:.6f} seconds")
print (g)

print('Starting haversine loop...')
start_time = time.perf_counter()
for r in range(0,5000000):
    g = inverse_haversine(45.23, -33.0, 35.22, -17)
elapsed = time.perf_counter() - start_time
print(f"Haversine loop execution time: {elapsed:.6f} seconds")
print (g)