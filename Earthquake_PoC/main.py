import datetime
import time
import os
import json

# Local modules
import fetch_earthquake
import archiver
import monitor
import alert_logger

def analyze_snapshot(target_dt=None, time_window_hours=24):
    """
    Main logic for a single "tick":
    1. Acquire data (Live or Archived).
    2. Analyze data.
    3. Return snapshot dict for UI.
    """
    data = None
    obs_time = None
    
    if target_dt:
        # Load from archive
        data, obs_time = archiver.load_data(target_dt)
        if not data:
            return None # Not found
    else:
        # Live fetch
        data, obs_time = fetch_earthquake.get_latest_earthquake()
        if data:
            # Save to archive
            archiver.save_data(data, obs_time)
            
    if not data:
        return {"error": "Failed to acquire data"}
        
    # Monitor / Analyze
    is_alert, risk_label, risk_desc = monitor.analyze_earthquake(data)
    
    # Log alert if live (target_dt is None) and it's an alert
    if target_dt is None and is_alert:
        # Simple duplicaton check could be added here, 
        # but for now rely on the logger acting on every call
        alert_logger.log_alert(
            timestamp_str=obs_time.strftime("%Y-%m-%d %H:%M:%S"),
            region=data.get("hypocenter", {}).get("name", "Unknown"),
            gup=data.get("hypocenter", {}).get("magnitude", 0), # Using Mag as GUP equivalent for now
            risk_label=risk_label,
            desc=risk_desc
        )

    # Construct Snapshot
    snapshot = {
        "timestamp": obs_time.strftime("%Y-%m-%d %H:%M:%S") if obs_time else "Unknown",
        "raw_data": data,
        "analysis": {
            "is_alert": is_alert,
            "risk_label": risk_label,
            "description": risk_desc
        },
        "predictions": monitor.generate_predictions(time_window_hours=time_window_hours)
    }
    
    return snapshot

if __name__ == "__main__":
    # Test run
    print("Running main.py test...")
    result = analyze_snapshot()
    print(json.dumps(result, indent=2, ensure_ascii=False))
