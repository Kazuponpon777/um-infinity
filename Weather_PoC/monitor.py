import time
import datetime
import csv
import os

# Import our existing UM-Infinity modules
import fetch_jma_data
import fetch_satellite
import fetch_space
import fetch_geomag
import fetch_urban_bio
import topology_engine
import visual_engine
import main
import archiver
import alert_logger

# Configuration
INTERVAL_SECONDS = 600  # Run every 10 minutes
RISK_THRESHOLD = 50.0   # Alert if GUP exceeds this
LOG_FILE = "um_infinity_log.csv"

def run_cycle(last_max_risk):
    print(f"\n[{datetime.datetime.now()}] Starting Monitoring Cycle...")
    obs_time = datetime.datetime.now() # Fallback
    
    # 1. Fetch Data
    data, obs_time = fetch_jma_data.fetch_all_data()
    
    if not data:
        print("No data fetched.")
        return 0.0
        
    # --- Persistence: Save Raw Data ---
    archiver.save_data(data, obs_time)
        
    # 2. Analyze
    engine = topology_engine.TopologicalEngine(data)
    results = engine.analyze()
    
    # 3. Global Factors
    space = fetch_space.get_solar_flux()
    geomag = fetch_geomag.get_geomag_index()
    urban = fetch_urban_bio.get_urban_factor(obs_time.hour)
    bio = fetch_urban_bio.get_bio_factor()
    
    global_factor = (1.0 + space) * (1.0 + geomag) * (1.0 + urban) * (1.0 + bio)
    
    processed_results = []
    max_risk = 0.0
    
    # Logic for Alerts
    ALERT_THRESHOLD = 50.0  # Threshold for logging history
    
    for res in results:
        hp = res['hydro_potential']
        # Simplified Cloud Factor for monitor (0.0 or fetch if needed)
        cf = 0.0 
        gup = hp * (1.0 + cf) * global_factor
        
        res['grand_potential'] = gup
        res['cloud_factor'] = cf
        
        abs_g = abs(gup)
        if abs_g > max_risk:
            max_risk = abs_g
            
        desc = main.get_risk_description(gup, hp, cf, space, geomag)
        
        # Determine Visuals
        risk_cls = "LOW"
        risk_label = "安全"
        if abs_g > 300: risk_cls="EXTREME"; risk_label="壊滅的"
        elif abs_g > 150: risk_cls="EXTREME"; risk_label="極めて危険"
        elif abs_g > 50: risk_cls="HIGH"; risk_label="危険"
        elif abs_g > 20: risk_cls="MODERATE"; risk_label="注意"
        
        # --- Persistence: Log High Risk ---
        if abs_g > ALERT_THRESHOLD:
            region_name = res.get('region', 'Unknown')
            alert_logger.log_alert(
                obs_time.strftime('%Y-%m-%d %H:%M:%S'),
                region_name,
                gup,
                risk_label,
                desc
            )
        
        res['desc'] = desc
        res['risk_cls'] = risk_cls
        res['risk_label'] = risk_label
        res['risk_color'] = "#50e3c2" # default
        
        processed_results.append(res)
        
        if abs(gup) > abs(max_risk):
            max_risk = gup

    # 4. Action: Logging & Alerting
    
    # CSV Log
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Max_GUP", "Location", "Space", "Geomag", "Bio"])
        writer.writerow([datetime.datetime.now(), f"{max_risk:.2f}", max_loc, space, geomag, bio])
        
    print(f"Cycle Complete. Max Risk: {max_risk:.2f} at {max_loc}")
    
    # Alert Logic
    if abs(max_risk) > RISK_THRESHOLD:
        print(f"!!! ALERT !!! Risk Level {abs(max_risk):.1f} exceeds threshold!")
        # Here we could send Line/Slack/Discord notification
        # send_notification(f"High Topological Risk detected: {max_risk}")

    # Trend Logic (Derivative)
    delta = abs(max_risk) - abs(last_max_risk)
    if delta > 20.0:
         print(f"!!! WARNING !!! Rapid Risk Escalation (+{delta:.1f}) detected!")

    # Update Report (Wrap as single snapshot for interactive dashboard)
    snapshot = {
        "timestamp": obs_time.strftime('%Y-%m-%d %H:%M:%S'),
        "display_name": f"{obs_time.strftime('%m/%d %H:%M')} (Monitor)",
        "space": space,
        "geomag": geomag,
        "urban": urban,
        "bio": bio,
        "results": sorted(processed_results, key=lambda x: abs(x['grand_potential']), reverse=True)[:50]
    }
    main.generate_interactive_report([snapshot])
    
    return max_risk

def start_monitor():
    print("=== UM-Infinity Continuous Monitoring Daemon ===")
    print(f"Interval: {INTERVAL_SECONDS}s | Log: {LOG_FILE}")
    print("Press Ctrl+C to stop.")
    
    last_risk = 0.0
    
    try:
        while True:
            last_risk = run_cycle(last_risk)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    start_monitor()
