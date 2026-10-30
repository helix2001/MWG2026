# mwg2026

<h1> Development branch </h1>
<h2>Code for the new risk calculation methods for MWG</h2>



Updated for MWG62

What's new

flight.py       -   Code maintenance and cleanup.
                    At Nabil's request, changed the proximity detection to look for 15 min ahead or behind,
                        and lateral to 30/60 NM, +/- 3NM, to keep it close to the current method.

calc.py         -   Updated the list of proximity pairs list with human readable values, also adding intermediate values, like proximity time.

mwg.py          -   Code maintenance and cleanup.

import_data.py  -   Improved the processing of time stamps, to allow for several formats to be correctly parsed.

report.py       -   Code maintenance and cleanup.
                    Improved the processing of time stamps, to allow for several formats to be correctly parsed.


<h1> Updated 2026-10-30 to start referencing the  document "FOX process v1.0" </h1>

Several files   -   Code cleanup and updated comments

geo_wgs84.py    -   Minor corrections and code cleanup
                    Added calculation for the average earth radius at a given location

geo.py          -   Removed all references to WGS84 calculations
                    Added calculation for the average earth radius at a given location
                    Minor corrections and code cleanup
_init_.py       -   Redefined several constants
                -   Optimized the definition of some constants

flight.py       -   Updated function check_proximity() to implement both 120NM and 15 minutes longitudinal definition.
                    The result of 120NM is not being tallied yet.
                    Used Haversine methods to calculate distances and bounding boxes

calc.py         -   Added graphical representation of the flights, for test purposes only


test_geo.py     -   Test bounding boxes methods, view graphical representation

legacy_calc_occupancy - removed legacy method to a standalone file