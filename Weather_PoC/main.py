import fetch_jma_data
import fetch_satellite
import fetch_space
import fetch_geomag
import fetch_urban_bio
import topology_engine
import visual_engine
import datetime
import argparse
import archiver

def analyze_snapshot(target_dt=None):
    """
    Analyzes a single time point and returns a result dict (snapshot).
    Returns None if data unavailable.
    """
    target_time = datetime.datetime.now()
    if target_dt:
        target_time = target_dt
        
    print(f"\n--- Analyzing Snapshot: {target_time} ---")
    
    # 1. Fetch Data (Try Archive -> Then API)
    data, obs_time = archiver.load_data(target_dt) if target_dt else (None, None)
    
    if not data:
        print("[Analysis] Not found in archive, fetching from JMA API...")
        data, obs_time = fetch_jma_data.fetch_all_data(target_dt)
    
    if not data:
        print(f"Skipping {target_time}: No data found.")
        return None
        
    # 2. visual/space data
    # (Using latest for consistency in PoC unless we upgrade fetchers)
    sat_res = fetch_satellite.fetch_latest_ir_image()
    vis_engine = None
    if sat_res:
         vis_engine = visual_engine.VisualEngine(sat_res[0], sat_res[2], sat_res[3], sat_res[4])

    space_factor = fetch_space.get_solar_flux()
    geomag_factor = fetch_geomag.get_geomag_index()
    urban_factor = fetch_urban_bio.get_urban_factor()
    bio_factor = fetch_urban_bio.get_bio_factor()
    
    global_factor = (1.0 + space_factor) * (1.0 + geomag_factor) * (1.0 + urban_factor) * (1.0 + bio_factor)
    
    # 3. Analyze
    engine = topology_engine.TopologicalEngine(data)
    results = engine.analyze()
    
    # 4. Enrich Results
    enriched_results = []
    for res in results:
        # Cloud Factor
        cf = 0.0
        if vis_engine:
            cf = vis_engine.get_cloud_factor(res['lat'], res['lon'])
            
        hp = res['hydro_potential']
        gup = hp * (1.0 + cf) * global_factor
        
        res['grand_potential'] = gup
        res['cloud_factor'] = cf
        
        # Determine Risk Color/Label
        abs_g = abs(gup)
        desc = get_risk_description(gup, hp, cf, space_factor, geomag_factor)
        
        risk_color = "#50e3c2"
        risk_label = "安全 (Low)"
        risk_cls = "LOW"
        if abs_g > 300: 
            risk_color = "#ff0055"; risk_label = "壊滅的 (CATACLYSMIC)"; risk_cls="EXTREME"
        elif abs_g > 150: 
            risk_color = "#ff5e3a"; risk_label = "極めて危険 (EXTREME)"; risk_cls="EXTREME"
        elif abs_g > 50: 
            risk_color = "#ff5e3a"; risk_label = "危険 (HIGH)"; risk_cls="HIGH"
        elif abs_g > 20: 
            risk_color = "#f5a623"; risk_label = "注意 (MODERATE)"; risk_cls="MODERATE"
            
        res['desc'] = desc
        res['risk_color'] = risk_color
        res['risk_label'] = risk_label
        res['risk_cls'] = risk_cls
        res['region'] = res.get('region', '洋上/観測点なし')
        
        enriched_results.append(res)
    
    # =========================================================================
    # UM_Infinity_V23: Sirius Protocol (シリウス・プロトコル)
    # =========================================================================
    import math
    FINE_STRUCTURE_CONSTANT_INV = 137  # α⁻¹ = 137
    
    # V23: Sector class for consciousness model
    class Sector:
        def __init__(self, material=0, mental=0, spiritual=0):
            self.material = material
            self.mental = mental
            self.spiritual = spiritual
        def to_dict(self):
            return {"material": round(self.material, 2), "mental": round(self.mental, 2), "spiritual": round(self.spiritual, 2)}
    
    # V23: UniverseTime cyclic modifier
    hour = datetime.datetime.now().hour
    phase = (hour - 6) * math.pi / 6
    cyclic_modifier = 1.0 + 0.2 * abs(math.sin(phase))
    
    # V23: Calculate torsion with Sector consciousness
    total_torsion = 0
    global_sector = Sector(0, 0, cyclic_modifier)
    
    for res in enriched_results:
        instability = abs(res.get('hydro_potential', 0)) / 50.0
        torsion_value = int(abs(res.get('grand_potential', 0)) * instability)
        res['torsion_value'] = torsion_value
        total_torsion += torsion_value
        
        # V23: Create Sector for each result
        sector = Sector(
            material=abs(res.get('grand_potential', 0)),
            mental=instability,
            spiritual=cyclic_modifier
        )
        res['sector'] = sector.to_dict()
        global_sector.material += sector.material
        global_sector.mental += sector.mental
    
    # Apply cyclic modifier
    total_torsion = round(total_torsion * cyclic_modifier, 2)
    
    # V23: Awaken status
    awaken_status = "DYNAMIC" if total_torsion != 0 else "STATIC"
    
    # V23: Sirius Final Proof
    sirius_proof = (FINE_STRUCTURE_CONSTANT_INV == 137) and (total_torsion != 0)
        
    # Return Snapshot with V23 metadata
    return {
        "timestamp": obs_time.strftime('%Y-%m-%d %H:%M:%S'),
        "display_name": f"{obs_time.strftime('%m/%d %H:%M')} (データ)",
        "space": space_factor,
        "geomag": geomag_factor,
        "urban": urban_factor,
        "bio": bio_factor,
        "results": sorted(enriched_results, key=lambda x: abs(x['grand_potential']), reverse=True)[:50],
        # V23 Sirius Metadata
        "v23_torsion": total_torsion,
        "v23_cyclic": round(cyclic_modifier, 2),
        "v23_threshold": FINE_STRUCTURE_CONSTANT_INV,
        "v23_awaken": awaken_status,
        "v23_sirius_proof": sirius_proof,
        "v23_sector": global_sector.to_dict(),
        "version": "V23"
    }

def main():
    parser = argparse.ArgumentParser(description='UM-Infinity Topological Weather Forecaster')
    parser.add_argument('--date', type=str, help='Target date in YYYY-MM-DD-HH format (e.g., 2024-01-01-12)')
    args = parser.parse_args()
    
    target_dt = None
    if args.date:
        try:
            target_dt = datetime.datetime.strptime(args.date, "%Y-%m-%d-%H")
            print(f"Time Machine Activated: Targeting {target_dt}")
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD-HH")
            return

    print("=== UM-Infinity Topological Weather Forecaster (Phase 6: Time Machine) ===")
    print(f"Time: {datetime.datetime.now()}")
    
    target_time = datetime.datetime.now()
    if target_dt:
        target_time = target_dt
        
    # Phase 7: Multi-Snapshot Storage
    snapshots = []
    
    # Define time points: [Target, Target-24h, Target-48h, Target-72h]
    time_points = [
        target_time,
        target_time - datetime.timedelta(hours=24),
        target_time - datetime.timedelta(hours=48)
    ]
    
    print("\n[Phase 7] Initiating Multi-Temporal Analysis Loop...")
    
    for t_idx, current_dt in enumerate(time_points):
        print(f"\n--- Processing Time Point [{t_idx+1}/{len(time_points)}]: {current_dt} ---")
        
        snap = analyze_snapshot(current_dt)
        if snap:
            snapshots.append(snap)

    if not snapshots:
        print("No valid snapshots generated.")
        return

    # Generate Interactive HTML
    generate_interactive_report(snapshots)


def get_risk_description(gup, hp, cloud, space, geomag):
    """Generates natural language description of the risk in Japanese."""
    desc = []
    
    # Base Phenomenon
    if abs(hp) > 50:
        if hp > 0: desc.append("猛烈な上昇気流（積乱雲の発達）")
        else: desc.append("強烈な下降気流（ダウンバースト・ウィンドシアー）")
    elif abs(hp) > 20:
        desc.append("大気が不安定")
        
    # Modifiers
    if cloud > 0.5:
        desc.append("発達した雨雲を伴う")
    elif cloud > 0.2:
        desc.append("雲の形成あり")
    elif abs(hp) > 20 and cloud < 0.1:
        desc.append("（晴天乱気流の可能性あり）")
        
    # Catalysts
    catalysts = []
    if space > 2.0: catalysts.append("宇宙線による核形成")
    if geomag > 0.6: catalysts.append("電離層圧力")
    
    if catalysts:
        cause = "・".join(catalysts)
        desc.append(f"要因: {cause}")
        
    # Disaster Type Prediction
    prediction = "通常の雨"
    if abs(gup) > 150: prediction = "【極限災害警報】ゲリラ豪雨・竜巻の恐れ"
    elif abs(gup) > 80: prediction = "【激しい嵐】"
    elif abs(gup) > 40: prediction = "【雷雨注意】"
    elif abs(gup) > 20: prediction = "急な雨"
    else: prediction = "平穏"
    
    full_text = f"<b>{prediction}</b><br>{' '.join(desc)}"
    return full_text

def generate_interactive_report(snapshots):
    # Use the latest snapshot's timestamp for "Report Generated Time"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare JSON Data Block
    import json
    # Custom serializer for datetime objects if needed, but we already converted to str
    snapshots_json = json.dumps(snapshots, ensure_ascii=False)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>UM-Infinity Time Machine Dashboard</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #1a1a1a; color: #e0e0e0; margin: 0; padding: 20px; }}
            h1 {{ border-bottom: 2px solid #50e3c2; padding-bottom: 10px; color: #50e3c2; font-size: 24px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: #252525; padding: 20px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
            
            #map {{ height: 600px; width: 100%; border-radius: 8px; margin-bottom: 20px; border: 1px solid #444; }}
            
            .controls {{ display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; }}
            .time-btn {{ background: #333; color: #fff; border: 1px solid #555; padding: 10px 20px; cursor: pointer; border-radius: 4px; transition: 0.3s; }}
            .time-btn:hover {{ background: #444; }}
            .time-btn.active {{ background: #50e3c2; color: #000; font-weight: bold; border-color: #50e3c2; }}
            
            .factors {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .card {{ background: #333; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }}
            .card h3 {{ margin: 0 0 5px 0; font-size: 0.8em; color: #aaa; }}
            .card .val {{ font-size: 1.4em; font-weight: bold; color: #fff; }}
            .card .desc {{ font-size: 0.7em; color: #888; margin-top: 5px; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9em; }}
            th {{ text-align: left; border-bottom: 1px solid #555; padding: 10px; color: #888; }}
            td {{ padding: 10px; border-bottom: 1px solid #333; }}
            tr:hover {{ background: #2a2a2a; }}
            
            .risk-LOW {{ color: #50e3c2; }}
            .risk-MODERATE {{ color: #f5a623; }}
            .risk-HIGH {{ color: #ff5e3a; font-weight: bold; }}
            .risk-EXTREME {{ color: #ff0055; font-weight: bold; text-shadow: 0 0 5px #ff0055; }}
            
            .desc-col {{ color: #ccc; }}
            .region-col {{ font-weight: bold; color: #fff; font-size: 1.1em; }}
            .coord-col {{ font-size: 0.8em; color: #777; }}
            
            .footer {{ margin-top: 30px; font-size: 0.8em; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>UM∞N 気象監視システム "The Eye" (Phase 7: Time Machine)</h1>
            <p style="text-align:center; color:#888;">
                レポート生成時刻: {timestamp} (JST)
            </p>
            
            <div class="controls" id="timeControls">
                <!-- Dynamically populated buttons -->
            </div>
            <p style="text-align:center; font-weight:bold; color:#50e3c2; margin-bottom: 20px;">
                表示中のデータ: <span id="currentDataLabel">---</span>
            </p>
            
            <div id="map"></div>
            
            <div class="factors">
                <div class="card"><h3>宇宙天気 (Space)</h3><div class="val" id="valSpace">-</div></div>
                <div class="card"><h3>地磁気 (Geomag)</h3><div class="val" id="valGeomag">-</div></div>
                <div class="card"><h3>都市 (Urban)</h3><div class="val" id="valUrban">-</div></div>
                <div class="card"><h3>心理 (Bio)</h3><div class="val" id="valBio">-</div></div>
            </div>
            
            <h2>リスク検出地域 (Top 20)</h2>
            <table>
                <thead>
                    <tr>
                        <th>地域 / 座標</th>
                        <th>AI予測・現象解説</th>
                        <th>気温 / 湿度</th>
                        <th>GUP指数</th>
                        <th>危険度</th>
                    </tr>
                </thead>
                <tbody id="riskTableBody">
                    <!-- Dynamic Content -->
                </tbody>
            </table>
            
            <div class="footer">
                解析理論: UM∞N (Information-Theoretic Quantum Gravity)<br>
                Interactive Time Machine v1.0
            </div>
        </div>

        <script>
            // --- Data Ingestion ---
            var snapshots = {snapshots_json};
            var map = null;
            var layerGroup = null;

            function initMap() {{
                map = L.map('map').setView([38.0, 137.0], 5);
                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                    subdomains: 'abcd',
                    maxZoom: 19
                }}).addTo(map);
                layerGroup = L.layerGroup().addTo(map);
            }}

            function renderSnapshot(index) {{
                var snap = snapshots[index];
                if(!snap) return;

                // 1. Update Labels
                document.getElementById('currentDataLabel').innerText = snap.timestamp + " (JST)";
                
                // 2. Update Controls Active State
                var btns = document.querySelectorAll('.time-btn');
                btns.forEach((b, i) => {{
                    if(i === index) b.classList.add('active');
                    else b.classList.remove('active');
                }});

                // 3. Update Factors
                document.getElementById('valSpace').innerText = snap.space.toFixed(2);
                document.getElementById('valGeomag').innerText = snap.geomag.toFixed(2);
                document.getElementById('valUrban').innerText = snap.urban.toFixed(2);
                document.getElementById('valBio').innerText = snap.bio.toFixed(2);

                // 4. Update Map
                layerGroup.clearLayers();
                snap.results.forEach(p => {{
                    var radius = Math.min(Math.abs(p.grand_potential) * 500, 50000);
                    if (radius < 5000) radius = 5000;
                    
                    var circle = L.circle([p.lat, p.lon], {{
                        color: p.risk_color,
                        fillColor: p.risk_color,
                        fillOpacity: 0.5,
                        radius: radius
                    }}).addTo(layerGroup);
                    
                    circle.bindPopup("<b>" + p.region + "</b><br>Risk: " + p.grand_potential.toFixed(1) + "<br>" + p.desc);
                }});

                // 5. Update Table
                var tbody = document.getElementById('riskTableBody');
                tbody.innerHTML = "";
                snap.results.slice(0, 20).forEach(res => {{
                    var tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>
                            <span class="region-col">${{res.region}}付近</span><br>
                            <span class="coord-col">${{res.lat.toFixed(3)}}, ${{res.lon.toFixed(3)}}</span>
                        </td>
                        <td class="desc-col">${{res.desc}}</td>
                        <td>
                            ${{res.temp.toFixed(1)}}℃<br>
                            ${{res.humidity.toFixed(0)}}%
                        </td>
                        <td><strong>${{res.grand_potential.toFixed(1)}}</strong></td>
                        <td class="risk-${{res.risk_cls}}">${{res.risk_label}}</td>
                    `;
                    tbody.appendChild(tr);
                }});
            }}

            function initControls() {{
                var container = document.getElementById('timeControls');
                snapshots.forEach((snap, idx) => {{
                    var btn = document.createElement('button');
                    btn.className = 'time-btn';
                    btn.innerText = snap.display_name;
                    btn.onclick = function() {{ renderSnapshot(idx); }};
                    container.appendChild(btn);
                }});
            }}

            // Start
            initMap();
            initControls();
            // Default to first (latest) snapshot
            if(snapshots.length > 0) renderSnapshot(0);
        </script>
    </body>
    </html>
    """
    
    with open("report.html", "w", encoding='utf-8') as f:
        f.write(html)
    print("\n[Share] Interactive Dashboard generated: report.html")

if __name__ == "__main__":
    main()
