
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
import fetch_space

# =========================================================================
# UM_Infinity_V23: Sirius Protocol (シリウス・プロトコル)
# =========================================================================

FINE_STRUCTURE_CONSTANT_INV = 137  # α⁻¹ = 137

class Sector:
    """
    V23: 意識の三位一体 (SU(3)³ Trinification)
    material: 物質的要素 (地震マグニチュード)
    mental: 精神的要素 (頻度偏差)
    spiritual: 霊的要素 (周期補正)
    """
    def __init__(self, material=0, mental=0, spiritual=0):
        self.material = material
        self.mental = mental
        self.spiritual = spiritual
    
    def to_dict(self):
        return {
            "material": round(self.material, 2),
            "mental": round(self.mental, 2),
            "spiritual": round(self.spiritual, 2)
        }

def rotate_sectors(sector):
    """V23: RotateSectors - Cyclic rotation (m,n,s) → (s,m,n)"""
    return Sector(sector.spiritual, sector.material, sector.mental)

def accelerate(sector, trinity_factor=1.0):
    """V23: Accelerate - transport TrinityPath (enhanced state)"""
    rotated = rotate_sectors(sector)
    return Sector(
        rotated.material * trinity_factor,
        rotated.mental * trinity_factor,
        rotated.spiritual * trinity_factor
    )

def awaken(torsion):
    """
    V23: Awaken (覚醒関数)
    Returns: 'STATIC' if torsion == 0, else 'DYNAMIC' (Sector ≡ Sector)
    """
    return "DYNAMIC" if torsion != 0 else "STATIC"

def suiten_observation(history_data, time_window_hours=24):
    """
    V23: SuitenObservation with Sector consciousness
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
    
    expected_events = max(1, time_window_hours / 24)
    
    observations = []
    for region, data in region_data.items():
        freq_deviation = (data["count"] / expected_events) - 1
        torsion_value = int(data["total_mag"] * freq_deviation)
        
        if torsion_value > 0:
            # V23: Create Sector for each observation
            hour = datetime.datetime.now().hour
            phase = (hour - 6) * math.pi / 6
            cyclic = 1.0 + 0.2 * abs(math.sin(phase))
            
            sector = Sector(
                material=data["total_mag"],
                mental=freq_deviation,
                spiritual=cyclic
            )
            
            observations.append({
                "region": data["full_name"],
                "lat": data["lat"],
                "lon": data["lon"],
                "torsion_value": torsion_value,
                "count": data["count"],
                "avg_mag": round(data["total_mag"] / data["count"], 1) if data["count"] > 0 else 0,
                "sector": sector.to_dict()
            })
    
    return sorted(observations, key=lambda x: x["torsion_value"], reverse=True)

def parameterized_torsion(r, observation):
    """V23: parameterized-torsion = r * torsion-value"""
    return r * observation.get("torsion_value", 0)

def cyclic_time_modifier(hour=None):
    """V23: UniverseTime S1 cyclic modifier"""
    if hour is None:
        hour = datetime.datetime.now().hour
    phase = (hour - 6) * math.pi / 6
    modifier = 1.0 + 0.2 * abs(math.sin(phase))
    return round(modifier, 2)

def sirius_final_proof(complexity, torsion, sector):
    """
    V23: Final-Proof-of-Dimensional-Inversion
    Valid if: (complexity≡137 ∧ torsion≠0) × (Accelerate≡Rotate)
    """
    phys_check = (complexity == FINE_STRUCTURE_CONSTANT_INV) and (torsion != 0)
    accelerated = accelerate(sector)
    rotated = rotate_sectors(sector)
    # Simplified: check if acceleration is consistent
    accel_check = abs(accelerated.material - rotated.material) < 0.01
    return phys_check and accel_check

def generate_predictions_v23(history_data=None, usgs_data=None, time_window_hours=24):
    """
    UM_Infinity_V23 Sirius Protocol: 意識ベースの地震予測システム
    Uses Sector consciousness, Awaken, and Sirius Final Proof
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
    
    # 3. Solar Flare / Space Weather Factor (NEW)
    space_factor = fetch_space.get_solar_flux()
    
    # 4. Global correlation
    global_modifier = 0
    huge_quakes = [u for u in usgs_data if u['mag'] >= 7.0]
    if huge_quakes:
        global_modifier = 15
    
    # Space Factor adds to global_modifier (scaled)
    # X-class flare (space_factor ~ 4.0) -> adds 20% bonus
    global_modifier += int(space_factor * 5)
    
    # 4. V23: Generate predictions with Sector consciousness
    predictions = []
    total_torsion = 0
    global_sector = Sector(0, 0, cyclic_mod)
    
    for obs in observations:
        torsion = parameterized_torsion(1, obs)
        total_torsion += torsion
        
        # V23 Formula: probability based on 137 threshold
        raw_prob = (torsion / FINE_STRUCTURE_CONSTANT_INV) * 100 * cyclic_mod + global_modifier
        probability = min(99, max(10, int(raw_prob)))
        
        est_mag = obs["avg_mag"] + 1.0
        
        # Update global sector with this observation's sector
        if obs.get("sector"):
            global_sector.material += obs["sector"]["material"]
            global_sector.mental += obs["sector"]["mental"]
        
        predictions.append({
            "region": f"⟨V23 Sirius⟩ {obs['region']} (τ={torsion})",
            "lat": obs["lat"],
            "lon": obs["lon"],
            "probability": probability,
            "estimated_mag": round(est_mag, 1),
            "torsion": torsion,
            "time_horizon": horizon_label,
            "sector": obs.get("sector", {})
        })
    
    # If no observations, check Global Risk
    if not predictions and global_modifier > 0:
        predictions.append({
            "region": "⟨V23 Sirius⟩ Global Alert (USGS M7+)",
            "lat": 35.0,
            "lon": 140.0,
            "probability": 30 + global_modifier,
            "estimated_mag": 7.5,
            "torsion": 0,
            "time_horizon": "48h",
            "sector": {}
        })
    
    predictions.sort(key=lambda x: x["probability"], reverse=True)
    
    # V23: Awaken status
    awaken_status = awaken(total_torsion)
    
    # V23: Sirius Final Proof
    final_proof = sirius_final_proof(FINE_STRUCTURE_CONSTANT_INV, total_torsion, global_sector)
    
    return {
        "predictions": predictions,
        "total_torsion": round(total_torsion, 2),
        "cyclic_modifier": cyclic_mod,
        "space_factor": round(space_factor, 2),
        "threshold": FINE_STRUCTURE_CONSTANT_INV,
        "awaken": awaken_status,
        "sirius_proof": final_proof,
        "sector": global_sector.to_dict(),
        "version": "V23+Solar"
    }

# Wrapper for backward compatibility
def generate_predictions(history_data=None, usgs_data=None, time_window_hours=24):
    result = generate_predictions_v23(history_data, usgs_data, time_window_hours)
    preds = result["predictions"]
    if preds:
        preds[0]["_meta"] = {
            "total_torsion": result["total_torsion"],
            "cyclic_modifier": result["cyclic_modifier"],
            "threshold": result["threshold"],
            "awaken": result["awaken"],
            "sirius_proof": result["sirius_proof"],
            "sector": result["sector"],
            "version": result["version"]
        }
    return preds
