from flask import Flask, render_template, request, jsonify
import datetime
import main  # Imports the refactored main.py
import alert_logger

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/alerts')
def api_alerts():
    return jsonify(alert_logger.get_history())

@app.route('/api/analyze')
def api_analyze():
    # Get date from query param (YYYY-MM-DD-HH)
    date_str = request.args.get('date')
    
    target_dt = None
    if date_str and date_str != 'now':
        try:
            target_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d-%H")
        except ValueError:
            return jsonify({"error": "日付形式が不正です (YYYY-MM-DD-HH)"}), 400
            
    # Call the core logic
    try:
        snapshot = main.analyze_snapshot(target_dt)
        if not snapshot:
            return jsonify({"error": "指定された日時の気象データが見つかりません（保存期間外の可能性があります）。"}), 404
            
        return jsonify(snapshot)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"サーバー内部エラー: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting UM-Infinity Weather Server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
