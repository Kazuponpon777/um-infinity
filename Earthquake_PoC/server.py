from flask import Flask, render_template, request, jsonify
import datetime
import sys
import os
import time
import threading

# Get absolute paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WEATHER_DIR = os.path.join(CURRENT_DIR, '..', 'Weather_PoC')

# Add paths for both modules
sys.path.insert(0, CURRENT_DIR)

import main as earthquake_main  # Earthquake main.py (local)
import alert_logger

# Import Weather main with proper path isolation
weather_main = None
try:
    # Save current path
    original_path = sys.path.copy()
    original_cwd = os.getcwd()
    
    # Change to Weather_PoC directory and import
    os.chdir(WEATHER_DIR)
    sys.path.insert(0, WEATHER_DIR)
    
    import importlib.util
    weather_main_spec = importlib.util.spec_from_file_location(
        "weather_main", 
        os.path.join(WEATHER_DIR, 'main.py')
    )
    weather_main = importlib.util.module_from_spec(weather_main_spec)
    weather_main_spec.loader.exec_module(weather_main)
    print("[OK] Weather module loaded successfully")
    
    # Restore path
    os.chdir(original_cwd)
except Exception as e:
    print(f"[Warning] Could not load Weather module: {e}")
    import traceback
    traceback.print_exc()
    weather_main = None

app = Flask(__name__)

# =========================================================================
# Data Cache (5-minute TTL)
# =========================================================================
CACHE_TTL_SECONDS = 300  # 5 minutes

class DataCache:
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < CACHE_TTL_SECONDS:
                    print(f"[Cache HIT] {key}")
                    return data
                else:
                    print(f"[Cache EXPIRED] {key}")
                    del self.cache[key]
            return None
    
    def set(self, key, data):
        with self.lock:
            self.cache[key] = (data, time.time())
            print(f"[Cache SET] {key}")

data_cache = DataCache()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/alerts')
def api_alerts():
    return jsonify(alert_logger.get_history())

@app.route('/api/analyze')
def api_analyze():
    """Earthquake Analysis API"""
    date_str = request.args.get('date')
    horizon = request.args.get('horizon', '24h')
    horizon_map = {'24h': 24, '1w': 168, '1m': 720, '6m': 4320, '1y': 8760}
    time_window_hours = horizon_map.get(horizon, 24)
    
    # Cache key
    cache_key = f"earthquake_{date_str}_{horizon}"
    cached = data_cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    target_dt = None
    if date_str and date_str != 'now':
        try:
            target_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d-%H")
        except ValueError:
            return jsonify({"error": "日付形式が不正です (YYYY-MM-DD-HH)"}), 400
            
    try:
        snapshot = earthquake_main.analyze_snapshot(target_dt, time_window_hours=time_window_hours)
        if not snapshot:
            return jsonify({"error": "データが見つかりません"}), 404
        snapshot["mode"] = "earthquake"
        data_cache.set(cache_key, snapshot)
        return jsonify(snapshot)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"サーバー内部エラー: {str(e)}"}), 500

@app.route('/api/weather/analyze')
def api_weather_analyze():
    """Weather Analysis API"""
    if weather_main is None:
        return jsonify({"error": "Weather module not available"}), 500
    
    date_str = request.args.get('date')
    
    # Cache key
    cache_key = f"weather_{date_str}"
    cached = data_cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    target_dt = None
    if date_str and date_str != 'now':
        try:
            target_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d-%H")
        except ValueError:
            return jsonify({"error": "日付形式が不正です"}), 400
            
    try:
        snapshot = weather_main.analyze_snapshot(target_dt)
        if not snapshot:
            return jsonify({"error": "気象データが見つかりません"}), 404
        snapshot["mode"] = "weather"
        data_cache.set(cache_key, snapshot)
        return jsonify(snapshot)
    except Exception as e:
        print(f"Weather Error: {e}")
        return jsonify({"error": f"気象サーバーエラー: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting UM-Infinity Unified Server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
