
"""
fetch_jaxa.py

JAXA (Japan Aerospace Exploration Agency) の衛星データ、特に
だいち(ALOS)シリーズの干渉SAR解析結果に基づく地殻変動情報を取得・管理するモジュール。

現在はAPI制限のため、模擬的なステータス返却を行う。
将来的に公式APIやRSSフィードと連携可能にする。
"""

import json
import os

# 模擬ステータスファイル (手動でTrueにしてテスト可能)
STATUS_FILE = os.path.join(os.path.dirname(__file__), "jaxa_status.json")

def _load_mock_status():
    """
    デバッグ用のステータスファイルを読み込む。
    なければデフォルト(正常)を作成して返す。
    """
    default_status = {
        "detected": False,
        "level": 0.0,
        "description": "No significant deformation detected.",
        "timestamp": "2026-01-18T00:00:00"
    }
    
    if not os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_status, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return default_status
        
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[JAXA] Error loading status file: {e}")
        return default_status

def get_sar_status() -> dict:
    """
    JAXA SARデータに基づく地殻変動ステータスを取得する。
    
    Returns:
        dict: {
            "detected": bool,       # 変動検知有無
            "risk_multiplier": float, # リスク係数 (通常1.0, 検知時1.5)
            "source": str,          # データソース名
            "description": str      # 詳細
        }
    """
    status = _load_mock_status()
    
    detected = status.get("detected", False)
    
    if detected:
        return {
            "detected": True,
            "risk_multiplier": 1.5,
            "source": "JAXA ALOS-2/4 (Daichi) InSAR",
            "description": status.get("description", "Significant Crustal Deformation Detected.")
        }
    else:
        return {
            "detected": False,
            "risk_multiplier": 1.0,
            "source": "JAXA ALOS-2/4 (Daichi)",
            "description": "Stable"
        }

if __name__ == "__main__":
    # Test run
    print(json.dumps(get_sar_status(), indent=2, ensure_ascii=False))
