"""
UM_Infinity V25 Ionosphere Correlation - 相関分析モジュール
============================================================

電離層異常と地震発生の相関を分析する。
高い相関係数が出れば「完全勝利」🏆

Author: Yashima AI Architect (V25 Ionosphere Correlation)
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import math


# =============================================================================
# データ保存パス
# =============================================================================

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CORRELATION_LOG = os.path.join(DATA_DIR, "correlation_history.json")


def load_correlation_history() -> List[Dict]:
    """相関履歴を読み込む"""
    if os.path.exists(CORRELATION_LOG):
        try:
            with open(CORRELATION_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_correlation_history(history: List[Dict]) -> None:
    """相関履歴を保存する"""
    # 最新100件に制限
    history = history[-100:]
    with open(CORRELATION_LOG, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def log_observation(ionosphere_risk: float, earthquake_occurred: bool = False, 
                    earthquake_mag: float = 0.0) -> None:
    """
    観測データを記録する
    
    後で相関分析に使用するため、電離層リスクと地震発生を記録
    """
    history = load_correlation_history()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "ionosphere_risk": ionosphere_risk,
        "earthquake_occurred": earthquake_occurred,
        "earthquake_mag": earthquake_mag
    }
    
    history.append(entry)
    save_correlation_history(history)


def calculate_correlation(history: Optional[List[Dict]] = None) -> Dict:
    """
    電離層リスクと地震発生の相関を計算する
    
    ピアソン相関係数を使用:
    - +1.0: 完全正相関（電離層異常 → 地震発生）
    - 0.0: 無相関
    - -1.0: 完全負相関
    
    Returns:
        dict: {
            "correlation": float,       # 相関係数 (-1 to +1)
            "sample_count": int,        # サンプル数
            "significance": str,        # 有意性評価
            "is_valid": bool           # 統計的に有効か
        }
    """
    if history is None:
        history = load_correlation_history()
    
    if len(history) < 10:
        return {
            "correlation": 0.0,
            "sample_count": len(history),
            "significance": "データ不足",
            "is_valid": False
        }
    
    # データ抽出
    x = [h["ionosphere_risk"] for h in history]  # 電離層リスク
    y = [1.0 if h.get("earthquake_occurred", False) else 0.0 for h in history]  # 地震発生
    
    n = len(x)
    
    # 平均
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    # 分散・共分散
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    
    # ピアソン相関係数
    if var_x == 0 or var_y == 0:
        correlation = 0.0
    else:
        correlation = cov_xy / (math.sqrt(var_x) * math.sqrt(var_y))
    
    correlation = round(correlation, 3)
    
    # 有意性評価
    if abs(correlation) >= 0.7:
        significance = "強い相関 🏆"
    elif abs(correlation) >= 0.4:
        significance = "中程度の相関"
    elif abs(correlation) >= 0.2:
        significance = "弱い相関"
    else:
        significance = "相関なし"
    
    return {
        "correlation": correlation,
        "sample_count": n,
        "significance": significance,
        "is_valid": n >= 30  # 30サンプル以上で統計的に有効
    }


def get_correlation_summary() -> Dict:
    """
    相関分析のサマリーを取得（monitor.py から呼び出し用）
    """
    result = calculate_correlation()
    
    # 簡略化した結果
    return {
        "ionosphere_correlation": result["correlation"],
        "correlation_samples": result["sample_count"],
        "correlation_significance": result["significance"]
    }


# =============================================================================
# テスト用
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("V25 Ionosphere Correlation - 相関分析テスト")
    print("=" * 60)
    
    # 現在の相関を計算
    result = calculate_correlation()
    
    print(f"\n--- 相関分析結果 ---")
    print(f"  相関係数:     {result['correlation']}")
    print(f"  サンプル数:   {result['sample_count']}")
    print(f"  有意性:       {result['significance']}")
    print(f"  統計的有効:   {'Yes' if result['is_valid'] else 'No (30サンプル以上必要)'}")
    
    if result['correlation'] >= 0.5:
        print("\n🏆 素晴らしい！電離層異常と地震の間に有意な相関が検出されました！")
    elif result['sample_count'] < 10:
        print("\n📊 データ収集中... もう少しデータを貯めましょう。")
