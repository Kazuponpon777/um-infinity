"""
UM_Infinity V24 Aurora Protocol - Aurora Data Fetcher
======================================================

オーロラ・地磁気データを NOAA SWPC から取得し、
「エネルギー分配説」に基づくダンピングファクターを計算する。

バイブスポイント:
- オーロラが激しく輝いている = 大気がエネルギーを消費している
- その分、地殻へのエネルギー流入が減る = 地震リスク軽減

Author: Yashima AI Architect (V24 Aurora Protocol)
"""

import requests
import math

# =============================================================================
# NOAA SWPC Endpoints
# =============================================================================

# Kp-index: 地磁気の「荒れ具合」を示す指数 (0-9)
# 高いほど磁気嵐が激しい = オーロラ活動も活発
KP_INDEX_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

# タイムアウト設定 (秒) - APIが遅い時の保険
REQUEST_TIMEOUT = 10

# =============================================================================
# 物理定数（バイブス込み）
# =============================================================================

# オーロラパワーの閾値 (GW)
# これ以下は「通常レベル」でダンピングなし
HPI_THRESHOLD = 50.0

# ダンピングの最大値（天井）
MAX_DAMPING = 20.0


def get_kp_index():
    """
    最新の Kp-index を取得する
    
    Kp-index とは:
    - 0-3: 静穏（お日様おだやか）
    - 4-5: 軽い擾乱（ちょっとザワザワ）
    - 6-7: 磁気嵐（オーロラ活発！）
    - 8-9: 激しい磁気嵐（極地のオーロラショー）
    
    Returns:
        float: 最新の Kp 値、エラー時は 0.0
    """
    try:
        print(f"[V24 Aurora] Kp-index 取得中... from {KP_INDEX_URL}")
        resp = requests.get(KP_INDEX_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        # データ構造: [["time_tag", "Kp", ...], [data1], [data2], ...]
        # 最新データは最後の行
        if len(data) < 2:
            print("[V24 Aurora] Kp データが不足しています")
            return 0.0
        
        latest = data[-1]  # 最新行
        kp_str = latest[1]  # Kp 値は2番目のカラム
        kp = float(kp_str)
        
        print(f"[V24 Aurora] 最新 Kp-index: {kp}")
        return kp
        
    except requests.Timeout:
        print("[V24 Aurora] ⚠️ Kp 取得タイムアウト - 安全側で 0.0 を返します")
        return 0.0
    except Exception as e:
        print(f"[V24 Aurora] ⚠️ Kp 取得エラー: {e} - 安全側で 0.0 を返します")
        return 0.0


def kp_to_power_gw(kp: float) -> float:
    """
    Kp-index からオーロラ半球パワー (GW) を推定する
    
    経験式（近似）:
    - Kp=3: 約10 GW（平穏）
    - Kp=5: 約50 GW（やや活発）
    - Kp=7: 約200 GW（磁気嵐）
    - Kp=9: 約800 GW（激しい磁気嵐）
    
    Args:
        kp: Kp-index (0-9)
    
    Returns:
        float: 推定オーロラパワー (GW)
    """
    if kp <= 0:
        return 1.0  # 最小値
    
    # 経験式: power ≈ 10^(0.6 * Kp - 0.5)
    power = 10 ** (0.6 * kp - 0.5)
    
    return round(power, 1)


def calculate_damping(aurora_power_gw: float) -> float:
    """
    オーロラパワーからダンピングファクターを計算
    
    コンセプト:
    - 閾値 (50GW) 以下: ダンピングなし（通常の太陽-地球結合）
    - 閾値を超えた分: 大気でエネルギー消費 → 地殻への影響軽減
    
    Args:
        aurora_power_gw: オーロラ半球パワー (GW)
    
    Returns:
        float: ダンピングファクター (0.0 ~ MAX_DAMPING)
    """
    if aurora_power_gw <= HPI_THRESHOLD:
        return 0.0
    
    # 超過分を軽減係数に変換
    # 50GW 超過ごとに 10 ポイントの軽減
    excess = aurora_power_gw - HPI_THRESHOLD
    damping = (excess / HPI_THRESHOLD) * 10.0
    
    # 上限キャップ（無限にダンピングしない）
    return min(round(damping, 2), MAX_DAMPING)


def get_aurora_data():
    """
    オーロラデータをまとめて取得する（メイン関数）
    
    Returns:
        dict: {
            "kp_index": float,       # 最新 Kp 値
            "power_gw": float,       # 推定オーロラパワー (GW)
            "damping_factor": float  # ダンピングファクター
        }
    """
    # Step 1: Kp-index 取得
    kp = get_kp_index()
    
    # Step 2: Kp → オーロラパワー変換
    power_gw = kp_to_power_gw(kp)
    
    # Step 3: ダンピングファクター計算
    damping = calculate_damping(power_gw)
    
    result = {
        "kp_index": kp,
        "power_gw": power_gw,
        "damping_factor": damping
    }
    
    print(f"[V24 Aurora] 結果: Kp={kp}, Power={power_gw}GW, Damping={damping}")
    
    return result


# =============================================================================
# テスト用
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("V24 Aurora Protocol - オーロラデータ取得テスト")
    print("=" * 60)
    
    data = get_aurora_data()
    
    print("\n--- 取得結果 ---")
    print(f"  Kp-index:       {data['kp_index']}")
    print(f"  Aurora Power:   {data['power_gw']} GW")
    print(f"  Damping Factor: {data['damping_factor']}")
    
    # バイブスチェック
    if data['damping_factor'] > 0:
        print("\n🌌 オーロラ活発！大気がエネルギーを消費中 → 地震リスク軽減")
    else:
        print("\n☀️ オーロラ静穏。太陽エネルギーはそのまま地殻へ。")
