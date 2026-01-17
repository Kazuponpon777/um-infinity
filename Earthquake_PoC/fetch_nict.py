"""
UM_Infinity V25 Ionosphere - NICT Data Fetcher (Japan)
======================================================
日本のNICT（情報通信研究機構）から宇宙天気情報を取得する。
我々の空（豊橋上空）を守るための重要なローカライズモジュール。

Source: https://swc.nict.go.jp/
"""

import requests
import re
from typing import Dict, Any, Optional

# NICT Targets
NICT_BASE_URL = "https://swc.nict.go.jp/"
NICT_IONOSPHERE_URL = "https://swc.nict.go.jp/trend/ionosphere.html"

# Timeout settings
REQUEST_TIMEOUT = 10

def _fetch_html(url: str) -> Optional[str]:
    """指定されたURLからHTMLを取得する"""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.encoding = response.apparent_encoding  # 日本語文字化け防止
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[V25 NICT] ⚠️ Connection failed to {url}: {e}")
        return None

def _analyze_text_risk(text: str, context_label: str = "") -> int:
    """
    テキスト内のキーワードからリスクレベルを判定する (0-3)
    
    Level 3: 臨時警報, 激しい, 警報 (Alert)
    Level 2: 活発 (Active)
    Level 1: やや活発 (Unstable?)
    Level 0: 静穏, データなし (Quiet)
    """
def _analyze_text_risk(text: str, context_label: str = "") -> int:
    """
    テキスト内のキーワードからリスクレベルを判定する (0-3)
    
    Level 3: 臨時警報, 激しい, 警報 (Alert)
    Level 2: 活発 (Active)
    Level 1: やや活発 (Unstable?)
    Level 0: 静穏, データなし (Quiet)
    """
    # 1. Cleaning: Remove Footer, Header, Nav, HEAD to avoid false positives
    # Simple regex to remove common structural blocks (non-greedy)
    cleaned_text = re.sub(r'<head>.*?</head>', '', text, flags=re.DOTALL)
    cleaned_text = re.sub(r'<footer.*?</footer>', '', cleaned_text, flags=re.DOTALL)
    cleaned_text = re.sub(r'<nav.*?</nav>', '', cleaned_text, flags=re.DOTALL)
    cleaned_text = re.sub(r'class="header".*?</div>', '', cleaned_text, flags=re.DOTALL)
    
    # Specific known false positives
    cleaned_text = cleaned_text.replace("臨時情報の発令基準", "") \
                               .replace("警報の基準", "") \
                               .replace("警報・注意報", "") \
                               .replace("<span>臨時情報</span>", "") # Menu item

    # 2. Keyword Counting
    # If a real alert exists, these words should appear in the main content area.
    
    # High Risk
    count_alert = cleaned_text.count("臨時情報") + cleaned_text.count("警報") + cleaned_text.count("激しい")
    
    # Medium Risk
    count_active = cleaned_text.count("活発")
    
    # Low Risk (Safe)
    count_quiet = cleaned_text.count("静穏")
    
    # Logic:
    # If "Alert" appears significantly, treat as Level 3.
    # Note: "警報" might appear in "警報はありません" (No warnings). 
    # So we should check for "警報" but assume safe if "静穏" dominates OR logic for "No Warning".
    
    # Improvement: Check for "No Warning" phrases
    if "警報はありません" in cleaned_text or "警報等はありません" in cleaned_text:
        count_alert = 0
    
    if count_alert > 0:
        # Check for negation if possible, but Japanese is hard to parse simply.
        # Assuming if "警報" appears in body (cleaned), it is likely an alert.
        # However, let's be conservative: if Quiet > Alert, maybe it's okay? 
        # But usually "Quiet" is for specific params, "Alert" is for overall.
        return 3
        
    if count_active > 0:
        return 2
        
    if "やや活発" in cleaned_text:
        return 1
    
    return 0

def get_nict_data() -> Dict[str, Any]:
    """
    NICTから電離圏およびデリンジャー現象の状況を取得する。
    
    Returns:
        dict: {
            "ionosphere_level": int (0-3),
            "dellinger_level": int (0-3),
            "risk_score": float (0.0 - 10.0),
            "source": "NICT",
            "location": "Japan/Aichi/Toyohashi"
        }
    """
    print(f"[V25 NICT] 🇯🇵 Fetching Space Weather Data from NICT...")
    
    # 1. Fetch Top Page or Trend Page
    # トップページの「現況」欄が最も情報がまとまっている可能性があるが、
    # 詳細ページの方がキーワードを拾いやすい場合もある。
    # 今回は確実性を高めるため、トップページから全体概況を取得する戦略をとる。
    html = _fetch_html(NICT_BASE_URL)
    
    if not html:
        return {
            "ionosphere_level": 0,
            "dellinger_level": 0,
            "risk_score": None, # Error state
            "error": "Connection Failed",
            "source": "NICT (Offline)"
        }
    
    # 2. Parse Specific Sections
    # HTML構造解析は壊れやすいため、特定のキーワード周辺を正規表現で切り出す
    
    # --- 電離圏 (Ionosphere) ---
    # 直近の電離圏概況を探す
    # 例: "電離圏嵐: 静穏" みたいな記述を探したいが、HTML構造による。
    # ここではHTML全体からリスクワードを探すが、誤検知を防ぐため
    # "電離圏" という単語の後の一定文字数をスキャンする
    ionosphere_level = 0
    ionosphere_matches = re.search(r'電離圏.*?<\/a>', html, re.DOTALL) # ナビゲーション等のリンク文字かもしれないが...
    
    # より広範囲に検索: '電離圏嵐' という単語が含まれるブロックを探す
    # シンプルに、ページ全体の頻出ワードから推定するロジック（簡易版）
    # ※厳密なスクレイピングより、"警報"が出ているかどうかが最重要
    
    # トップページに「警報」や「臨時情報」が出ている場合は全体リスクとする
    top_alert_level = _analyze_text_risk(html[:5000]) # ヘッダー付近の重要情報
    
    # 個別ページも確認（念のため）
    trend_html = _fetch_html(NICT_IONOSPHERE_URL)
    if trend_html:
        ionosphere_level = _analyze_text_risk(trend_html)
    else:
        ionosphere_level = top_alert_level

    # --- デリンジャー現象 ---
    # 現時点では個別のデリンジャー情報を取得するURLを叩くか、トップページの"デリンジャー"周辺を見る
    # 簡易的にトップページ判定結果を利用（もしトップに警報があればデリンジャーの可能性も含むため）
    dellinger_level = top_alert_level # 仮の実装
    
    # 3. Calculate Final Risk Score
    # Max Level を採用
    max_level = max(ionosphere_level, dellinger_level, top_alert_level)
    
    # Mapping
    # 0 -> 0.0
    # 1 -> 2.5
    # 2 -> 5.0
    # 3 -> 10.0
    risk_map = {0: 0.0, 1: 2.5, 2: 5.0, 3: 10.0}
    risk_score = risk_map.get(max_level, 0.0)
    
    result = {
        "ionosphere_level": ionosphere_level,
        "dellinger_level": dellinger_level,
        "risk_score": risk_score,
        "source": "NICT (National Institute of Information and Communications Technology)",
        "location": "Japan/Aichi/Toyohashi"
    }
    
    print(f"[V25 NICT] Result: Level={max_level} (Risk {risk_score})")
    return result

if __name__ == "__main__":
    # Test run
    data = get_nict_data()
    print("--------------------------------------------------")
    print(f"Location: {data['location']}")
    print(f"Source:   {data['source']}")
    print(f"Risk:     {data['risk_score']}")
    print(f"Details:  Ionosphere={data['ionosphere_level']}, Dellinger={data['dellinger_level']}")
    print("--------------------------------------------------")
