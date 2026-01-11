import json
import os
import datetime

HISTORY_FILE = "alert_history.json"

def log_alert(timestamp_str, region, gup, risk_label, desc):
    """
    Appends a new alert to the history file.
    """
    new_entry = {
        "timestamp": timestamp_str,
        "region": region,
        "gup": float(gup),
        "risk_label": risk_label,
        "desc": desc
    }
    
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
            
    # Prepend new alert (newest first)
    history.insert(0, new_entry)
    
    # Limit to last 100 alerts
    history = history[:100]
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"[Logger] Alert logged: {region} (GUP: {gup})")

def get_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []
