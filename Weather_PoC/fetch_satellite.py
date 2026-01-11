import requests
import json
import datetime
import os

# JMA Himawari Endpoints
TARGET_TIMES_URL = "https://www.jma.go.jp/bosai/himawari/data/satimg/targetTimes_fd.json"
TILE_BASE_URL = "https://www.jma.go.jp/bosai/himawari/data/satimg/{basetime}/fd/{validtime}/{band}/{prod}/{z}/{x}/{y}.jpg"

# Parameters for Japan Area (Approximate)
# Zoom Level 5 seems appropriate for regional analysis?
# At z=5, the world is 32x32 tiles? No, standard TMS is 2^z.
# JMA uses 2^z tiles for width?
# Let's try z=4 (16x16 world). Japan is roughly at x=13, y=5?
# Let's verify standard web mercator.
# Lat 35, Lon 135.
# n = 2^z
# x = n * (lon + 180) / 360
# y = n * (1 - log(tan + sec) / pi) / 2
# For z=4:
# x = 16 * (135+180)/360 = 16 * 315/360 = 14
# y... around 6?
#
# Actually, JMA URLs might differ slightly or follow standard XYZ.
# Let's just grab a known tile or try to match lat/lon.
#
# Band 13 (B13) is IR. TBB (Temperature Black Body).
# This gives us cloud top temperature. Lower (Whiter/Brighter in std display) = Higher Altitude = More Energy.
#
# For this PoC, we will fetch ONE tile that covers the main island (Honshu).
# Z=5, X=27, Y=12 covers central Japan well?
# Let's implement a tile calculator.

def latlon_to_tile(lat, lon, z):
    import math
    n = 2.0 ** z
    xtile = int((lon + 180.0) / 360.0 * n)
    rad_lat = math.radians(lat)
    ytile = int((1.0 - math.log(math.tan(rad_lat) + (1.0 / math.cos(rad_lat))) / math.pi) / 2.0 * n)
    return xtile, ytile

def fetch_latest_ir_image(save_path="satellite_ir.jpg"):
    try:
        # 1. Get List of Times
        resp = requests.get(TARGET_TIMES_URL)
        resp.raise_for_status()
        times_list = resp.json()
        
        if not times_list:
            print("No satellite times found.")
            return None
            
        # Latest time
        latest = times_list[-1]
        basetime = latest['basetime']
        validtime = latest['validtime']
        
        print(f"Latest Satellite Time: {basetime}")
        
        # 2. Determine Tile
        # Target: Central Japan (35N, 137E)
        z = 5
        x, y = latlon_to_tile(35.0, 137.0, z)
        print(f"Target Tile (z={z}): x={x}, y={y}")
        
        # 3. Construct URL
        # Pattern: .../B13/TBB/{z}/{x}/{y}.jpg
        url = TILE_BASE_URL.format(
            basetime=basetime,
            validtime=validtime,
            band="B13",
            prod="TBB",
            z=z,
            x=x,
            y=y
        )
        print(f"Fetching Tile URL: {url}")
        
        img_resp = requests.get(url)
        img_resp.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(img_resp.content)
            
        print(f"Saved IR image to {save_path}")
        return save_path, basetime, z, x, y
        
    except Exception as e:
        print(f"Error fetching satellite image: {e}")
        return None

if __name__ == "__main__":
    fetch_latest_ir_image()
