import math

class TopologicalEngine:
    def __init__(self, data_points):
        self.data_points = data_points
        self.grid = {}
        self.resolution = 0.25 # degrees (approx 25km)

    def interpolate_to_grid(self):
        """Simple IDW interpolation to a regular lat/lon grid."""
        if not self.data_points:
            return

        lats = [d['lat'] for d in self.data_points]
        lons = [d['lon'] for d in self.data_points]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Create grid points
        lat_steps = int((max_lat - min_lat) / self.resolution) + 1
        lon_steps = int((max_lon - min_lon) / self.resolution) + 1
        
        print(f"Generating Grid: {lat_steps} x {lon_steps}")
        
        for i in range(lat_steps):
            lat = min_lat + i * self.resolution
            for j in range(lon_steps):
                lon = min_lon + j * self.resolution
                
                # Inverse Distance Weighting
                w_u, w_v, w_temp, w_humid = 0, 0, 0, 0
                total_weight = 0
                
                found_neighbor = False
                
                # For finding nearest station name
                min_dist_for_name = float('inf')
                nearest_name = "Unknown"
                
                for point in self.data_points:
                    d = math.sqrt((lat - point['lat'])**2 + (lon - point['lon'])**2)
                    if d < 0.0001: d = 0.0001
                    
                    # Update nearest name
                    if d < min_dist_for_name:
                        min_dist_for_name = d
                        nearest_name = point.get('name', 'Unknown')
                    
                    if d > 1.0: 
                        continue
                        
                    weight = 1.0 / (d**2)
                    w_u += point['u'] * weight
                    w_v += point['v'] * weight
                    # Handle missing temp/humid
                    p_temp = point.get('temp') or 15.0 # Default fallback
                    p_humid = point.get('humidity') or 60.0 # Default fallback
                    
                    w_temp += p_temp * weight
                    w_humid += p_humid * weight
                    
                    total_weight += weight
                    found_neighbor = True
                
                if found_neighbor and total_weight > 0:
                    self.grid[(i, j)] = {
                        'lat': lat,
                        'lon': lon,
                        'u': w_u / total_weight,
                        'v': w_v / total_weight,
                        'temp': w_temp / total_weight,
                        'humidity': w_humid / total_weight,
                        'region': nearest_name
                    }
                    
    def calculate_winding_density(self):
        """Calculates discrete curl (vorticity) and Hydro-Topological Potential."""
        results = []
        
        for k, cell in self.grid.items():
            i, j = k
            
            if (i+1, j) in self.grid and (i, j+1) in self.grid:
                c  = cell
                cN = self.grid[(i+1, j)]
                cE = self.grid[(i, j+1)]
                
                dy = (cN['lat'] - c['lat']) 
                dx = (cE['lon'] - c['lon']) * math.cos(math.radians(c['lat']))
                
                if dx == 0 or dy == 0: continue

                du = cN['u'] - c['u']
                dv = cE['v'] - c['v']
                
                d_v_dx = dv / dx
                d_u_dy = du / dy
                
                curl = d_v_dx - d_u_dy
                
                # Hydro-Topological Potential
                # P = |Curl| * f(Humidity)
                # If Humidity > 90%, multiplier is huge.
                # If Humidity < 50%, multiplier is small.
                
                humid = c['humidity']
                
                # Sigmoid-like factor for humidity
                # 80% -> 1.0, 100% -> 5.0, 50% -> 0.1
                hydro_factor = max(0.0, (humid - 50.0) / 10.0)
                if humid > 90: hydro_factor *= 2.0
                
                potential = curl * hydro_factor
                
                results.append({
                    'lat': c['lat'],
                    'lon': c['lon'],
                    'winding_density': curl,
                    'hydro_potential': potential,
                    'temp': c['temp'],
                    'humidity': c['humidity'],
                    'region': c['region']
                })
                
        return results

    def analyze(self):
        print("Interpolating wind field...")
        self.interpolate_to_grid()
        print("Calculating topological invariants (Winding Density)...")
        results = self.calculate_winding_density()
        return results
