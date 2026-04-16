# mwg2026

<h1> Development branch <h1>

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