"""
UM_Infinity V25 Ionosphere Correlation - 電離層データ取得モジュール
===================================================================

電離層TEC (Total Electron Content) の異常を検出し、
地震前兆の可能性を評価する。

バイブスポイント:
- 電離層は地球の「電気的バリア」
- 地震（人工・自然問わず）の前には電離層に異常が出る
- この共通項を捉えれば「完全勝利」

Author: Yashima AI Architect (V25 Ionosphere Correlation)
"""

import requests
import re
from typing import List, Tuple

# =============================================================================
# NOAA SWPC Endpoints
# =============================================================================

# US-TEC Recent Trend: 過去10日平均との差分
# 異常値が大きい = 電離層が乱れている = 地震前兆の可能性
TEC_TREND_URL = "https://services.swpc.noaa.gov/text/us-tec-recent-trend.txt"

# タイムアウト設定 (秒)
REQUEST_TIMEOUT = 15

# =============================================================================
# 閾値設定（バイブス込み）
# =============================================================================

# TEC異常の閾値 (TECU: TEC Units)
# この値を超えると「要注意」
TEC_ANOMALY_THRESHOLD = 30  # ±30 TECU以上で異常とみなす

# 電離層リスクの最大値
MAX_IONOSPHERE_RISK = 10.0


def parse_tec_trend_data(raw_text: str) -> List[Tuple[int, List[int]]]:
    """
    US-TEC Recent Trend のテキストデータをパースする
    
    フォーマット: 各行が緯度とTEC変動値のグリッド
    例: "340   -30   -23   -14   ..."
    
    Returns:
        List of (latitude, [tec_values])
    """
    result = []
    lines = raw_text.strip().split('\n')
    
    for line in lines:
        # 数値のみの行を抽出
        line = line.strip()
        if not line or line.startswith(':') or line.startswith('#'):
            continue
        
        # 数値を抽出
        numbers = re.findall(r'-?\d+', line)
        if len(numbers) < 10:  # 最低10個の値がある行のみ
            continue
        
        try:
            lat = int(numbers[0])
            values = [int(n) for n in numbers[1:]]
            result.append((lat, values))
        except ValueError:
            continue
    
    return result


def get_tec_anomaly() -> dict:
    """
    US-TEC Recent Trend を取得し、電離層異常を検出する
    
    Returns:
        dict: {
            "max_anomaly": float,       # 最大異常値 (TECU)
            "min_anomaly": float,       # 最小異常値 (TECU)
            "anomaly_count": int,       # 閾値超過グリッド数
            "total_grids": int,         # 総グリッド数
            "anomaly_ratio": float,     # 異常グリッド比率
            "ionosphere_risk": float    # 電離層リスク係数 (0-10)
        }
    """
    try:
        print(f"[V25 Ionosphere] TEC Trend データ取得中... from {TEC_TREND_URL}")
        resp = requests.get(TEC_TREND_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        
        # データをパース
        data = parse_tec_trend_data(resp.text)
        
        if not data:
            print("[V25 Ionosphere] ⚠️ TEC データのパースに失敗")
            return _default_result()
        
        # 全TEC値を集計
        all_values = []
        for lat, values in data:
            all_values.extend(values)
        
        if not all_values:
            return _default_result()
        
        # 統計計算
        max_anomaly = max(all_values)
        min_anomaly = min(all_values)
        
        # 閾値を超える異常グリッドをカウント
        anomaly_count = sum(1 for v in all_values if abs(v) > TEC_ANOMALY_THRESHOLD)
        total_grids = len(all_values)
        anomaly_ratio = anomaly_count / total_grids if total_grids > 0 else 0
        
        # 電離層リスク係数を計算
        # 最大異常値と異常比率の両方を考慮
        max_abs = max(abs(max_anomaly), abs(min_anomaly))
        
        # リスク計算: (最大異常/100) + (異常比率 * 5)
        risk = (max_abs / 100) * 5 + (anomaly_ratio * 5)
        ionosphere_risk = min(round(risk, 2), MAX_IONOSPHERE_RISK)
        
        result = {
            "max_anomaly": max_anomaly,
            "min_anomaly": min_anomaly,
            "anomaly_count": anomaly_count,
            "total_grids": total_grids,
            "anomaly_ratio": round(anomaly_ratio, 3),
            "ionosphere_risk": ionosphere_risk
        }
        
        print(f"[V25 Ionosphere] 結果: Max={max_anomaly} TECU, Anomaly={anomaly_count}/{total_grids}, Risk={ionosphere_risk}")
        
        return result
        
    except requests.Timeout:
        print("[V25 Ionosphere] ⚠️ TEC データ取得タイムアウト")
        return _default_result()
    except Exception as e:
        print(f"[V25 Ionosphere] ⚠️ TEC データ取得エラー: {e}")
        return _default_result()


def _default_result() -> dict:
    """エラー時のデフォルト結果（安全側評価）"""
    return {
        "max_anomaly": 0,
        "min_anomaly": 0,
        "anomaly_count": 0,
        "total_grids": 0,
        "anomaly_ratio": 0.0,
        "ionosphere_risk": 0.0
    }


def get_ionosphere_data() -> dict:
    """
    電離層データをまとめて取得する（メイン関数）
    
    fetch_aurora.py との互換性を保つインターフェース
    
    Returns:
        dict: 電離層異常データ
    """
    return get_tec_anomaly()


# =============================================================================
# テスト用
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("V25 Ionosphere Correlation - 電離層データ取得テスト")
    print("=" * 60)
    
    data = get_ionosphere_data()
    
    print("\n--- 取得結果 ---")
    print(f"  最大異常値:     {data['max_anomaly']} TECU")
    print(f"  最小異常値:     {data['min_anomaly']} TECU")
    print(f"  異常グリッド:   {data['anomaly_count']} / {data['total_grids']}")
    print(f"  異常比率:       {data['anomaly_ratio'] * 100:.1f}%")
    print(f"  電離層リスク:   {data['ionosphere_risk']}")
    
    # バイブスチェック
    if data['ionosphere_risk'] > 3.0:
        print("\n⚡ 電離層に異常検出！地震前兆の可能性あり")
    elif data['ionosphere_risk'] > 1.0:
        print("\n🌐 電離層にやや変動あり。注視中。")
    else:
        print("\n✅ 電離層は安定。異常なし。")
