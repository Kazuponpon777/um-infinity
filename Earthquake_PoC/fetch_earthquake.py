import requests
import json
import datetime

# P2P Quake API (JSON)
# https://www.p2pquake.net/json_api_v2/
API_URL = "https://api.p2pquake.net/v2/history"

def get_latest_earthquake():
    """
    Fetches the latest earthquake information (code 551) from P2P Quake API.
    Returns a unified data dictionary or None if failed.
    """
    params = {
        "codes": "551",  # 551: Earthquake Information
        "limit": 1
    }
    
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data_list = response.json()
        
        if not data_list:
            return None
            
        latest = data_list[0]
        
        # Parse timestamp
        # Format example: "2024/01/01 12:34:56"
        time_str = latest.get("time")
        if time_str:
            # Handle potential milliseconds (e.g., "2024/01/01 12:34:56.789")
            # Truncate to first 19 chars for standard strptime
            obs_time = datetime.datetime.strptime(time_str[:19], "%Y/%m/%d %H:%M:%S")
        else:
            obs_time = datetime.datetime.now()
            
        # Extract key info for monitoring
        earthquake_info = latest.get("earthquake", {})
        hypocenter = earthquake_info.get("hypocenter", {})
        
        result = {
            "source": "P2P Quake",
            "time": time_str,
            "id": latest.get("id"),
            "code": latest.get("code"),
            "issue_type": latest.get("issue", {}).get("type"),
            "hypocenter": {
                "name": hypocenter.get("name"),
                "magnitude": hypocenter.get("magnitude"),
                "depth": hypocenter.get("depth"),
                "latitude": hypocenter.get("latitude"),
                "longitude": hypocenter.get("longitude")
            },
            "max_scale": earthquake_info.get("maxScale"), # Intensity (shindo) * 10 or generic value
            "points": latest.get("points", []), # Intensity data by region
            "raw_data": latest # Keep raw for full context if needed
        }
        
        return result, obs_time

    except Exception as e:
        print(f"[Fetch Earthquake] Error: {e}")
        return None, None

def get_earthquake_history(limit=50):
    """
    Fetches the recent history of earthquakes.
    Returns: List of simplified quake dicts [{time, name, mag, scale}]
    """
    params = {
        "codes": "551",
        "limit": limit
    }
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        data_list = response.json()
        
        history = []
        for item in data_list:
            eq = item.get("earthquake", {})
            hypo = eq.get("hypocenter", {})
            history.append({
                "time": item.get("time"),
                "name": hypo.get("name"),
                "magnitude": hypo.get("magnitude", 0),
                "max_scale": eq.get("maxScale", 0),
                "lat": hypo.get("latitude"),
                "lon": hypo.get("longitude")
            })
        return history
    except Exception as e:
        print(f"[Fetch History] Error: {e}")
        return []

def get_usgs_data():
    """
    Fetches significant earthquakes (M4.5+) from USGS (US Geological Survey) for Global Analysis.
    Returns: List of dicts [{place, mag, time, url}]
    """
    # USGS GeoJSON Summary Feed (M4.5+ Past Day)
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        features = data.get("features", [])
        usgs_list = []
        for f in features:
            props = f.get("properties", {})
            # time is epoch ms
            dt = datetime.datetime.fromtimestamp(props.get("time")/1000.0)
            usgs_list.append({
                "place": props.get("place"),
                "mag": props.get("mag"),
                "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "url": props.get("url")
            })
        return usgs_list
    except Exception as e:
        print(f"[Fetch USGS] Error: {e}")
        return []

if __name__ == "__main__":
    # Test run
    data, time = get_latest_earthquake()
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"Timestamp: {time}")
    else:
        print("Failed to fetch data.")
