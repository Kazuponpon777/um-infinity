
import datetime
def analyze_earthquake(data):
    """
    Analyzes the earthquake data and returns a risk assessment.
    Returns: (is_alert, risk_label, description)
    """
    if not data:
        return False, "NO DATA", "No data available."
        
    max_scale = data.get("max_scale", 0)
    hypocenter = data.get("hypocenter", {})
    magnitude = hypocenter.get("magnitude", -1.0)
    location = hypocenter.get("name", "Unknown")
    
    # Scale conversion (P2P Quake uses scale * 10 mostly, or raw values. 
    # Usually: 10=Shindo 1, 20=Shindo 2, 30=Shindo 3, 40=Shindo 4, 45=Shindo 5-, 50=5+, 55=6-, 60=6+, 70=7)
    # If magnitude is float, handle gracefully.
    
    try:
        mag_val = float(magnitude)
    except:
        mag_val = 0.0
        
    try:
        scale_val = int(max_scale)
    except:
        scale_val = 0
        
    # Logic defining "Alert" (Adjust as per user requirement)
    # Let's say Shindo 3+ (scale >= 30) or Magnitude >= 5.0 is noteworthy.
    
    is_alert = False
    risk_label = "INFO"
    
    if scale_val >= 50: # Shindo 5+
        is_alert = True
        risk_label = "DANGER"
    elif scale_val >= 30: # Shindo 3
        is_alert = True
        risk_label = "WARNING"
    elif mag_val >= 5.0:
        is_alert = True
        risk_label = "CAUTION"
        
    description = f"Location: {location}, Mag: {magnitude}, Max Intensity: {scale_val/10}"
    
    return is_alert, risk_label, description

import random
import math

import fetch_earthquake

# =========================================================================
# UM_Infinity_V20 Framework Functions
# =========================================================================

def calculate_torsion(history_data, time_window_hours=24):
    """
    UM_Infinity_V20: Calculate Crust Torsion (地殻歪み指数).
    Torsion = Σ(magnitude × frequency_deviation)
    where frequency_deviation = (events_in_region / expected_events) - 1
    """
    now = datetime.datetime.now()
    region_data = {}
    
    for q in history_data:
        try:
            q_time = datetime.datetime.strptime(q['time'][:19], "%Y/%m/%d %H:%M:%S")
            if (now - q_time).total_seconds() > time_window_hours * 3600:
                continue
        except:
            continue
            
        region = q.get('name', 'Unknown')[:3]
        mag = q.get('magnitude', 0) or 0
        
        if region not in region_data:
            region_data[region] = {"count": 0, "total_mag": 0, "lat": q.get('lat'), "lon": q.get('lon'), "full_name": q.get('name', 'Unknown')}
        region_data[region]["count"] += 1
        region_data[region]["total_mag"] += mag
    
    # Calculate torsion per region
    # Expected events: 1 per 24h as baseline (scaled by time_window)
    expected_events = max(1, time_window_hours / 24)
    
    torsion_results = []
    for region, data in region_data.items():
        freq_deviation = (data["count"] / expected_events) - 1
        torsion = data["total_mag"] * freq_deviation
        if torsion > 0:  # Only consider positive torsion (accumulating stress)
            torsion_results.append({
                "region": data["full_name"],
                "lat": data["lat"],
                "lon": data["lon"],
                "torsion": round(torsion, 2),
                "count": data["count"],
                "avg_mag": round(data["total_mag"] / data["count"], 1) if data["count"] > 0 else 0
            })
    
    return sorted(torsion_results, key=lambda x: x["torsion"], reverse=True)

def cyclic_risk_modifier(hour=None):
    """
    UM_Infinity_V20: S1 Cyclic Time Model.
    Risk oscillates following cosmic rhythm (peaks at 6:00 and 18:00 JST).
    Returns: modifier between 0.8 and 1.2
    """
    if hour is None:
        hour = datetime.datetime.now().hour
    # Sin wave with peaks at 6 and 18 (every 12 hours)
    # Phase shift: peak at 6 → sin((hour - 6) * π / 6)
    phase = (hour - 6) * math.pi / 6
    modifier = 1.0 + 0.2 * abs(math.sin(phase))
    return round(modifier, 2)

def generate_predictions_v20(history_data=None, usgs_data=None, time_window_hours=24):
    """
    UM_Infinity_V20: Torsion-based Earthquake Prediction.
    Uses crust torsion index and cyclic time model with 137 threshold.
    """
    if history_data is None:
        history_data = fetch_earthquake.get_earthquake_history(limit=100)
    if usgs_data is None:
        usgs_data = fetch_earthquake.get_usgs_data()
    
    # Time horizon label
    horizon_labels = {24: "24h", 168: "1週間", 720: "1ヶ月", 4320: "半年", 8760: "1年"}
    horizon_label = horizon_labels.get(time_window_hours, f"{time_window_hours}h")
    
    # 1. Calculate Torsion for all regions
    torsion_data = calculate_torsion(history_data, time_window_hours)
    
    # 2. Get cyclic risk modifier (S1 time model)
    cyclic_mod = cyclic_risk_modifier()
    
    # 3. Global correlation
    global_modifier = 0
    huge_quakes = [u for u in usgs_data if u['mag'] >= 7.0]
    if huge_quakes:
        global_modifier = 15  # Increase risk if global M7+ detected
    
    # 4. Generate predictions using 137 threshold
    predictions = []
    total_torsion = 0
    
    for t in torsion_data:
        torsion = t["torsion"]
        total_torsion += torsion
        
        # V20 Formula: probability = (torsion / 137) * 100 * cyclic_mod + global_mod
        raw_prob = (torsion / 137) * 100 * cyclic_mod + global_modifier
        probability = min(99, max(10, int(raw_prob)))
        
        # Estimated magnitude: average + 1.0 buffer
        est_mag = t["avg_mag"] + 1.0
        
        predictions.append({
            "region": f"⟨V20⟩ {t['region']} (τ={t['torsion']})",
            "lat": t["lat"],
            "lon": t["lon"],
            "probability": probability,
            "estimated_mag": round(est_mag, 1),
            "torsion": t["torsion"],
            "time_horizon": horizon_label
        })
    
    # If no regional torsion, check Global Risk
    if not predictions and global_modifier > 0:
        predictions.append({
            "region": "⟨V20⟩ Global Seismic Alert (USGS M7+)",
            "lat": 35.0,
            "lon": 140.0,
            "probability": 30 + global_modifier,
            "estimated_mag": 7.5,
            "torsion": 0,
            "time_horizon": "48h"
        })
    
    predictions.sort(key=lambda x: x["probability"], reverse=True)
    
    # Append total torsion as metadata
    return {
        "predictions": predictions,
        "total_torsion": round(total_torsion, 2),
        "cyclic_modifier": cyclic_mod,
        "threshold": 137
    }

# Wrapper for backward compatibility
def generate_predictions(history_data=None, usgs_data=None, time_window_hours=24):
    result = generate_predictions_v20(history_data, usgs_data, time_window_hours)
    # For backward compat, return just predictions list with torsion info embedded
    preds = result["predictions"]
    # Add metadata to first item for UI access
    if preds:
        preds[0]["_meta"] = {
            "total_torsion": result["total_torsion"],
            "cyclic_modifier": result["cyclic_modifier"],
            "threshold": result["threshold"]
        }
    return preds
