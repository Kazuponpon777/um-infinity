import requests
import json
import math

# NOAA SWPC Data
# GOES X-ray Flux (6-hour, 1-minute averaged)
# Updated URL: primary/xrays-6-hour.json might be case sensitive or changed.
# Using 'json/goes/primary/xrays-6-hour.json'
XRAY_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"

def get_solar_flux():
    """Fetches the latest X-ray flux from NOAA."""
    try:
        print(f"Fetching Solar Data from: {XRAY_URL}")
        resp = requests.get(XRAY_URL)
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            return 0.0
            
        # Latest data point
        latest = data[-1]
        flux = latest['flux'] # Watts/m^2
        
        # Logarithmic scale mapping
        # Normal (Quiet) ~ 10^-8 -> Factor 0.0
        # X-class (10^-4) -> Factor 4.0
        
        if flux <= 0: return 0.0
        
        log_flux = math.log10(flux)
        factor = max(0.0, log_flux + 8.0)
        
        print(f"Latest Solar Flux: {flux} (Log: {log_flux:.2f}) -> Space Factor: {factor:.2f}")
        return factor
        
    except Exception as e:
        print(f"Error fetching solar data: {e}. Returning 0.0")
        return 0.0

if __name__ == "__main__":
    get_solar_flux()
