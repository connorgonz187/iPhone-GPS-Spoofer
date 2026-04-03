iOS Location Simulator — Setup & Usage Instructions
====================================================

REQUIREMENTS
------------
- Windows PC
- iPhone with Developer Mode enabled
- Python 3.11 or 3.12  (NOT 3.13 — see note below)
- iTunes installed from the Microsoft Store (not Apple's website)
  Microsoft Store link: search "iTunes" in the Store app
- Microsoft C++ Build Tools (required to compile one dependency)
  Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
  During install, select "Desktop development with C++" -> Install (~5 GB)
  Restart your terminal after install completes.

NOTE ON PYTHON VERSION
----------------------
The lzfse package (a dependency) has no pre-built installer for Python 3.13.
It must be compiled from source, which requires the C++ Build Tools above.
Python 3.12 works without any compiler. Download from https://www.python.org/downloads/


FIRST-TIME SETUP (do once)
--------------------------
1. Install Microsoft C++ Build Tools (see REQUIREMENTS above).

2. Install iTunes from the Microsoft Store and open it at least once.

3. Install Python dependencies:
   Open a terminal and run:
       pip install -r requirements.txt

4. Enable Developer Mode on iPhone:
   Settings -> Privacy & Security -> Developer Mode -> toggle ON -> Restart

5. Plug iPhone into PC via USB.
   When prompted on the iPhone, tap "Trust This Computer" and enter your passcode.

6. Pair the device (run once per device):
       python -m pymobiledevice3 lockdown pair

7. Copy the example config and fill in your coordinates:
   - Copy config.toml.example and rename the copy to config.toml
   - Open config.toml and replace the placeholder coordinates with:
       [home]  -> your actual home latitude and longitude
       [away]  -> a location at least 500 meters away from home

   To find your coordinates: open Google Maps, right-click your home, copy the numbers.
   First number = latitude, second = longitude.


EVERY TIME YOU USE IT
---------------------
1. Right-click start_tunneld.bat -> "Run as administrator"
   Keep that window open the entire time. Do not close it.

2. Plug in your iPhone via USB (if not already connected).

3. Run one of the commands below from a normal terminal.


COMMANDS
--------
Simulate arriving home (triggers "arrive" automations):
    python location_sim.py enter

Simulate leaving home (triggers "leave" automations):
    python location_sim.py leave

Return iPhone to real GPS location:
    python location_sim.py restore


TESTING IT WORKS
----------------
1. Run: python location_sim.py enter
2. Open Maps on the iPhone — the location pin should jump to your home coordinates.
3. Run: python location_sim.py restore
4. The pin should return to your real location.

If the pin moves correctly, geofence automations will fire.
After running "enter", wait up to 60 seconds for automations to trigger.


TROUBLESHOOTING
---------------
"failed-wheel-build" / "error: lzfse" during pip install
  -> No pre-built package exists for your Python version (3.13+).
     Option A: Install Microsoft C++ Build Tools (see REQUIREMENTS), restart terminal, retry.
     Option B: Install Python 3.12 from python.org, then retry pip install.


"Cannot reach tunneld"
  -> start_tunneld.bat is not running, or was not run as Administrator.

"No devices found"
  -> iPhone is not plugged in, or you have not tapped "Trust This Computer" on the device.

"config.toml not found"
  -> You need to copy config.toml.example to config.toml.

Automation does not fire after "enter"
  -> Run "leave" first, wait 10 seconds, then run "enter" again.
     Automations trigger on the transition (entering the zone), not just being inside it.
  -> Make sure your [away] coordinates are at least 500m from [home].

"NotPairedError" or pairing error
  -> Re-run: pymobiledevice3 usbmux pair
     Then unplug and replug the iPhone.
