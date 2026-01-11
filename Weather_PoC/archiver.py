import os
import json
import datetime
import fetch_jma_data

ARCHIVE_ROOT = "archive"

def save_data(data, obs_time):
    """
    Saves the fetched JMA data dict to a local JSON file.
    Structure: archive/YYYY/MM/DD/YYYYMMDDHHMMSS.json
    """
    if not data:
        return None
        
    # Create directory structure
    year = obs_time.strftime('%Y')
    month = obs_time.strftime('%m')
    day = obs_time.strftime('%d')
    
    dir_path = os.path.join(ARCHIVE_ROOT, year, month, day)
    os.makedirs(dir_path, exist_ok=True)
    
    # Filename
    filename = f"{obs_time.strftime('%Y%m%d%H%M%S')}.json"
    file_path = os.path.join(dir_path, filename)
    
    # Save
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        
    print(f"[Archiver] Saved data to {file_path}")
    return file_path

def load_data(target_dt):
    """
    Attempts to load data from local archive for a specific timestamp (rounded to 10 mins).
    Returns (data, obs_time) or (None, None).
    """
    # Round target_dt to 10 mins
    minute = target_dt.minute - (target_dt.minute % 10)
    dt = target_dt.replace(minute=minute, second=0, microsecond=0)
    
    year = dt.strftime('%Y')
    month = dt.strftime('%m')
    day = dt.strftime('%d')
    filename = f"{dt.strftime('%Y%m%d%H%M%S')}.json"
    
    file_path = os.path.join(ARCHIVE_ROOT, year, month, day, filename)
    
    if os.path.exists(file_path):
        print(f"[Archiver] Loaded from cache: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, dt
    else:
        return None, None
