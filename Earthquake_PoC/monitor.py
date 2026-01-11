
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
# UM_Infinity_V21 Framework Functions (萃点システム)
# =========================================================================

CONSTANT_137 = 137  # Universe resolution threshold

def suiten_observation(history_data, time_window_hours=24):
    """
    UM_Infinity_V21: SuitenObservation (萃点観測)
    Returns observation records with torsion-value and prediction-prob
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
            region_data[region] = {
                "count": 0, "total_mag": 0, 
                "lat": q.get('lat'), "lon": q.get('lon'), 
                "full_name": q.get('name', 'Unknown')
            }
        region_data[region]["count"] += 1
        region_data[region]["total_mag"] += mag
    
    # Calculate SuitenObservation per region
    expected_events = max(1, time_window_hours / 24)
    
    observations = []
    for region, data in region_data.items():
        freq_deviation = (data["count"] / expected_events) - 1
        torsion_value = int(data["total_mag"] * freq_deviation)  # ℤ in V21
        
        if torsion_value > 0:
            observations.append({
                "region": data["full_name"],
                "lat": data["lat"],
                "lon": data["lon"],
                "torsion_value": torsion_value,  # V21: SuitenObservation.torsion-value
                "count": data["count"],
                "avg_mag": round(data["total_mag"] / data["count"], 1) if data["count"] > 0 else 0
            })
    
    return sorted(observations, key=lambda x: x["torsion_value"], reverse=True)

def parameterized_torsion(r, observation):
    """
    UM_Infinity_V21: parameterized-torsion
    Returns: r * torsion-value (scaling factor)
    """
    return r * observation.get("torsion_value", 0)

def cyclic_time_modifier(hour=None):
    """
    UM_Infinity_V21: UniverseTime (S1 循環的時間)
    Linear order is impossible on S1 → cyclic risk pattern
    """
    if hour is None:
        hour = datetime.datetime.now().hour
    phase = (hour - 6) * math.pi / 6
    modifier = 1.0 + 0.2 * abs(math.sin(phase))
    return round(modifier, 2)

def is_consistent(complexity, torsion):
    """
    UM_Infinity_V21: Consistency check
    Valid if: complexity ≡ 137 ∧ torsion ≠ 0
    """
    return complexity == CONSTANT_137 and torsion != 0

def generate_predictions_v21(history_data=None, usgs_data=None, time_window_hours=24):
    """
    UM_Infinity_V21: 萃点ベースの地震予測システム
    Uses SuitenObservation, parameterized-torsion, and consistency proof
    """
    if history_data is None:
        history_data = fetch_earthquake.get_earthquake_history(limit=100)
    if usgs_data is None:
        usgs_data = fetch_earthquake.get_usgs_data()
    
    # Time horizon label
    horizon_labels = {24: "24h", 168: "1週間", 720: "1ヶ月", 4320: "半年", 8760: "1年"}
    horizon_label = horizon_labels.get(time_window_hours, f"{time_window_hours}h")
    
    # 1. V21: Get SuitenObservation (萃点観測)
    observations = suiten_observation(history_data, time_window_hours)
    
    # 2. V21: UniverseTime cyclic modifier
    cyclic_mod = cyclic_time_modifier()
    
    # 3. Global correlation
    global_modifier = 0
    huge_quakes = [u for u in usgs_data if u['mag'] >= 7.0]
    if huge_quakes:
        global_modifier = 15
    
    # 4. V21: Generate predictions with parameterized_torsion
    predictions = []
    total_torsion = 0
    
    for obs in observations:
        # Apply parameterized torsion with r=1
        torsion = parameterized_torsion(1, obs)
        total_torsion += torsion
        
        # V21 Formula: probability based on 137 threshold
        raw_prob = (torsion / CONSTANT_137) * 100 * cyclic_mod + global_modifier
        probability = min(99, max(10, int(raw_prob)))
        
        # Estimated magnitude
        est_mag = obs["avg_mag"] + 1.0
        
        predictions.append({
            "region": f"⟨V21萃点⟩ {obs['region']} (τ={torsion})",
            "lat": obs["lat"],
            "lon": obs["lon"],
            "probability": probability,
            "estimated_mag": round(est_mag, 1),
            "torsion": torsion,
            "time_horizon": horizon_label
        })
    
    # If no observations, check Global Risk
    if not predictions and global_modifier > 0:
        predictions.append({
            "region": "⟨V21萃点⟩ Global Alert (USGS M7+)",
            "lat": 35.0,
            "lon": 140.0,
            "probability": 30 + global_modifier,
            "estimated_mag": 7.5,
            "torsion": 0,
            "time_horizon": "48h"
        })
    
    predictions.sort(key=lambda x: x["probability"], reverse=True)
    
    # V21: Check consistency (complexity≡137 ∧ torsion≠0)
    consistency = is_consistent(CONSTANT_137, total_torsion)
    
    return {
        "predictions": predictions,
        "total_torsion": round(total_torsion, 2),
        "cyclic_modifier": cyclic_mod,
        "threshold": CONSTANT_137,
        "is_consistent": consistency,
        "version": "V21"
    }

# Wrapper for backward compatibility
def generate_predictions(history_data=None, usgs_data=None, time_window_hours=24):
    result = generate_predictions_v21(history_data, usgs_data, time_window_hours)
    preds = result["predictions"]
    if preds:
        preds[0]["_meta"] = {
            "total_torsion": result["total_torsion"],
            "cyclic_modifier": result["cyclic_modifier"],
            "threshold": result["threshold"],
            "is_consistent": result["is_consistent"],
            "version": result["version"]
        }
    return preds

