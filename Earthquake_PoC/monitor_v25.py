
import json
import os
import datetime
import math
import sys

# Ensure Earthquake_PoC is in path if running from root
sys.path.append(os.path.join(os.getcwd(), "Earthquake_PoC"))

try:
    from Earthquake_PoC import fetch_earthquake, fetch_space, fetch_aurora, fetch_nict, fetch_jaxa, correlation_analyzer
    from Earthquake_PoC.monitor import Sector, parameterized_torsion, cyclic_time_modifier, awaken, sirius_final_proof, suiten_observation
except ImportError:
    # If running directly inside Earthquake_PoC
    import fetch_earthquake, fetch_space, fetch_aurora, fetch_nict, fetch_jaxa, correlation_analyzer
    from monitor import Sector, parameterized_torsion, cyclic_time_modifier, awaken, sirius_final_proof, suiten_observation

CACHE_FILE = "v25_metrics_cache.json"
FINE_STRUCTURE_CONSTANT_INV = 137

class V25Monitor:
    def __init__(self):
        self.cache = self._load_cache()
        self.current_metrics = {}
        
    def _load_cache(self):
        """Load previous metrics for trend analysis."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Save current metrics for next run."""
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.current_metrics, f)

    def get_trend(self, key, current_value, threshold=0.1):
        """
        Calculate trend arrow based on previous value.
        Returns: "↗", "↘", or "→"
        """
        prev_value = self.cache.get(key, current_value)
        delta = current_value - prev_value
        
        # Store for next time
        self.current_metrics[key] = current_value
        
        if delta > threshold:
            return "↗" # Rank Up / Rising
        elif delta < -threshold:
            return "↘" # Rank Down / Dropping
        else:
            return "→" # Stable

    def get_solar_class(self, flux):
        """Map flux factor to Solar Flare Class (Simulated/Approx)."""
        # Note: True flux is F10.7 or Watts/m2. Here we map our factor (0-5.0).
        if flux < 1.0: return "A-Class (Quiet)"
        if flux < 1.5: return "B-Class (Weak)"
        if flux < 3.0: return "C-Class (Moderate)"
        if flux < 5.0: return "M-Class (Strong)"
        return "X-Class (Extreme)"

    def get_alert_level(self, total_score):
        """Determine alert level based on Total Risk Score."""
        if total_score < 30: return "NORMAL"
        if total_score < 50: return "CAUTION"
        if total_score < 80: return "WARNING"
        return "DANGER"

    def run(self):
        try:
            # 1. Fetch Data
            space_factor = fetch_space.get_solar_flux()
            aurora_data = fetch_aurora.get_aurora_data()
            ionosphere_data = fetch_nict.get_nict_data()
            sar_status = fetch_jaxa.get_sar_status()
            
            # 2. Extract Key Metrics
            aurora_power = aurora_data.get("power_gw", 0)
            damping_factor = aurora_data["damping_factor"]
            ionosphere_risk = ionosphere_data["risk_score"]
            sar_detected = sar_status["detected"]
            
            # 3. Calculate Trends (Task 1)
            trend_space = self.get_trend("space_factor", space_factor, 0.1)
            trend_aurora = self.get_trend("aurora_power", aurora_power, 5.0) # Power fluctuates more
            trend_iono = self.get_trend("ionosphere_risk", ionosphere_risk, 0.5)
            
            # 4. Calculate Risk Components (Task 2 & 3)
            
            # --- Structural Stress (Task 2) ---
            structural_stress = 20.0 if sar_detected else 0.0
                
            # --- Trigger Score (Task 3) ---
            # Solar
            raw_solar = space_factor * 5
            net_solar_bonus = max(0, raw_solar - damping_factor)
            
            # Ionosphere Filter
            filter_status = "True Signal" if (space_factor < 1.5 and ionosphere_risk > 5.0) else "Normal"
            filter_status = "Solar Cancelled" if space_factor > 3.0 else filter_status
            
            final_iono_risk = ionosphere_risk
            if filter_status == "Solar Cancelled":
                final_iono_risk *= 0.2
            elif filter_status == "True Signal": # Map "True Signal" to specific string if needed, logic above used 'True Signal DETECTED'
                final_iono_risk *= 2.0
                
            trigger_score = net_solar_bonus + final_iono_risk
            
            # --- Total Risk ---
            # Base Risk (from Torsion) is calculated per region, but for the global summary:
            # We assume a nominal base risk or derive it from the highest torsion
            history = fetch_earthquake.get_earthquake_history(limit=100)
            observations = suiten_observation(history)
            
            max_torsion_prob = 0
            cyclic_mod = cyclic_time_modifier()
            
            predictions = []
            if observations:
                # Calculate max torsion probability for 'base' metric
                obs = observations[0]
                torsion = parameterized_torsion(1, obs)
                base_prob = (torsion / FINE_STRUCTURE_CONSTANT_INV) * 100 * cyclic_mod
                max_torsion_prob = int(base_prob)
            
            base_risk = max_torsion_prob # Use the highest local torsion as the "Base" for header stats
            total_score = base_risk + structural_stress + trigger_score
            
            # Apply to all predictions
            for obs in observations:
                torsion = parameterized_torsion(1, obs)
                base_p = (torsion / FINE_STRUCTURE_CONSTANT_INV) * 100 * cyclic_mod
                final_p = min(99, max(10, int(base_p + structural_stress + trigger_score)))
                predictions.append({
                    "region": obs['region'],
                    "probability": final_p,
                    "mag": round(obs["avg_mag"] + 1.0, 1),
                    "torsion": torsion
                })
                
            predictions.sort(key=lambda x: x["probability"], reverse=True)
            
            # 5. Save Cache
            self._save_cache()
            
            # 6. Output Result (Task 4 Schema)
            result = {
              "version": "V25 Final",
              "timestamp": datetime.datetime.now().isoformat(),
              "status": {
                "solar": {
                    "value": round(space_factor, 2),
                    "trend": trend_space,
                    "class": self.get_solar_class(space_factor)
                },
                "aurora": {
                    "value": round(aurora_power, 1),
                    "trend": trend_aurora,
                    "damping": round(damping_factor, 1)
                },
                "ionosphere": {
                    "value": round(ionosphere_risk, 1),
                    "trend": trend_iono,
                    "source": "NICT",
                    "condition": filter_status
                }
              },
              "risk_metrics": {
                "base": round(base_risk, 1),
                "structural": structural_stress,
                "trigger": round(trigger_score, 1),
                "total_score": round(total_score, 1)
              },
              "alert_level": self.get_alert_level(total_score),
              "top_predictions": predictions[:3]
            }
            
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
            
        except Exception as e:
            # Robust Error Handling
            err_result = {
                "version": "V25 Final",
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e),
                "alert_level": "UNKNOWN"
            }
            print(json.dumps(err_result, indent=2, ensure_ascii=False))
            return err_result

if __name__ == "__main__":
    monitor = V25Monitor()
    monitor.run()
