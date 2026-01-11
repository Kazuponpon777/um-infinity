import requests
import json
import datetime

# NOAA SWPC Planetary K-index
# https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json
Kp_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

def get_geomag_index():
    """Fetches the latest Kp index."""
    try:
        print(f"Fetching Geomagnetic Data from: {Kp_URL}")
        resp = requests.get(Kp_URL)
        resp.raise_for_status()
        data = resp.json()
        
        # Data format is list of lists
        # [["time_tag", "Kp", "a_running", "station_count"], ...]
        if not data or len(data) < 2:
            return 0.0
            
        # Last entry
        latest = data[-1]
        # Kp is index 1
        kp_str = latest[1]
        kp = float(kp_str)
        
        # Kp ranges 0-9.
        # 0-2 Quiet
        # 3-4 Unsettled
        # 5+ Storm
        
        # Factor: normalize 0-9 to 0.0-1.0 (or higher)
        # In UM-Infinity, high geomagnetic disturbance = Ionosphere trouble = Factor > 0.5?
        # Let's just use Kp / 5.0 as a factor. (Kp=5 -> 1.0)
        
        factor = kp / 5.0
        
        print(f"Latest Kp Index: {kp} -> Geomag Factor: {factor:.2f}")
        return factor
        
    except Exception as e:
        print(f"Error fetching geomag data: {e} (Using default 0.0)")
        return 0.0 # Default

if __name__ == "__main__":
    get_geomag_index()
