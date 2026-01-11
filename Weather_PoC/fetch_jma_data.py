import requests
import json
import datetime
import math

# JMA Endpoints
LATEST_TIME_URL = "https://www.jma.go.jp/bosai/amedas/data/latest_time.txt"
STATION_LIST_URL = "https://www.jma.go.jp/bosai/amedas/const/amedastable.json"
# Map endpoint format: https://www.jma.go.jp/bosai/amedas/data/map/{YYYYMMDDHHMM}00.json
# Note: The latest_time.txt gives YYYY-MM-DDTHH:MM:SS+09:00 format.

def get_latest_timestamp():
    """Fetches the latest available data timestamp from JMA."""
    try:
        response = requests.get(LATEST_TIME_URL)
        response.raise_for_status()
        # Format example: 2023-10-27T10:00:00+09:00
        iso_str = response.text.strip()
        dt = datetime.datetime.fromisoformat(iso_str)
        return dt
    except Exception as e:
        print(f"Error fetching latest timestamp: {e}")
        return None

def get_station_data():
    """Fetches the list of AMeDAS stations."""
    try:
        response = requests.get(STATION_LIST_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching station list: {e}")
        return {}

def get_observation_data(dt):
    """Fetches weather observation data for a specific timestamp."""
    try:
        # Format timestamp for URL: YYYYMMDDHHMM00
        time_str = dt.strftime("%Y%m%d%H%M00")
        url = f"https://www.jma.go.jp/bosai/amedas/data/map/{time_str}.json"
        print(f"Fetching data from: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching observation data: {e}")
        return {}

def wind_direction_to_vector(angle_deg, speed):
    """Converts wind speed and direction (degrees) to U, V components.
    JMA Wind Direction: 0 is calm, usually 1-16 (N=16, E=4, S=8, W=12).
    Let's assume the JSON provides raw degrees or we need to map 16 sectors.
    Actually, JMA map JSON often returns raw values.
    Checked JMA specs: 
    'windDirection': 
      0: Calm
      1: NNE, 2: NE, ... 8: S ... 16: N
    Wait, usually standard is:
    1: NNE, ... 4: E, ... 8: S, ... 12: W, ... 16: N
    But let's double check if we get degrees or indices. 
    Usually 'temp' is [value, quality]. 'wind' is [direction, speed].
    NO, commonly: 'wind': [speed, direction_code]
    """
    if speed is None or angle_deg is None:
        return 0.0, 0.0
    
    # Map JMA 16-direction code to degrees
    # 0: Calm
    # 1: NNE (22.5)
    # ...
    # 4: E   (90)
    # 8: S   (180)
    # 12: W  (270)
    # 16: N  (360/0)
    
    if angle_deg == 0:
        return 0.0, 0.0
        
    degree = angle_deg * 22.5
    
    # Mathematical Angle (radians, counter-clockwise from East)
    # Wind blows FROM the direction.
    # U = -speed * sin(theta)
    # V = -speed * cos(theta)
    # where theta is compass angle (0 is North, 90 East).
    
    rad = math.radians(degree)
    
    # Meteorological Wind Vector (blowing TO)
    # If wind is North (blowing from North), it pushes South.
    # u (East-West): -speed * sin(rad)
    # v (North-South): -speed * cos(rad)
    
    u = -speed * math.sin(rad)
    v = -speed * math.cos(rad)
    
    return u, v

def fetch_all_data(target_dt=None):
    """Main function to unify data."""
    if target_dt:
        # Round down to nearest 10 minutes
        minute = target_dt.minute - (target_dt.minute % 10)
        dt = target_dt.replace(minute=minute, second=0, microsecond=0)
        print(f"Target data time (rounded): {dt}")
    else:
        dt = get_latest_timestamp()
    
    if not dt:
        return [], None
    
    print(f"Latest data time: {dt}")
    
    stations = get_station_data()
    observations = get_observation_data(dt)
    
    unified_data = []
    
    for station_id, obs in observations.items():
        if station_id not in stations:
            continue
            
        st_info = stations[station_id]
        
        # Structure of obs: {'temp': [20.5, 0], 'wind': [3.4, 12], ...}
        # wind: [speed, direction]
        # pressure: [pressure, quality] (optional)
        
        wind_data = obs.get('wind')
        if not wind_data:
            continue
            
        speed = wind_data[0]
        direction_code = wind_data[1]
        
        # Filter valid data
        if speed is None or direction_code is None:
            continue

        lat = st_info.get('lat')
        lon = st_info.get('lon')
        
        # JMA lat/lon are [degrees, minutes] often.
        # "lat": [35, 41.2], "lon": [139, 45.6]
        # Need to convert to decimal
        lat_dec = lat[0] + lat[1]/60.0
        lon_dec = lon[0] + lon[1]/60.0
        
        u, v = wind_direction_to_vector(direction_code, speed)
        
        # Pressure (if available)
        pressure_data = obs.get('pressure')
        pressure = pressure_data[0] if pressure_data else None

        # Temperature
        temp_data = obs.get('temp')
        temp = temp_data[0] if temp_data else None

        # Humidity
        humid_data = obs.get('humidity')
        humidity = humid_data[0] if humid_data else None

        unified_data.append({
            'station_id': station_id,
            'name': st_info.get('kjName'),
            'lat': lat_dec,
            'lon': lon_dec,
            'u': u,
            'v': v,
            'pressure': pressure,
            'temp': temp,
            'humidity': humidity,
            'wind_speed': speed,
            'wind_dir_code': direction_code
        })
        
    return unified_data, dt

if __name__ == "__main__":
    data, dt = fetch_all_data()
    print(f"Fetched {len(data)} data points.")
    if len(data) > 0:
        print(f"Sample: {data[0]}")
