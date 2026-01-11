import random
import datetime

def get_urban_factor():
    """Simulates Urban Heat/Energy Topology based on time of day."""
    now = datetime.datetime.now()
    hour = now.hour
    
    # Simple heuristic:
    # High energy usage 08:00 - 20:00 (Factor ~ 0.8 - 1.0)
    # Peak at 12:00 and 18:00
    # Low at regular times.
    
    if 8 <= hour <= 20:
        base = 0.8
        if 11 <= hour <= 13 or 17 <= hour <= 19:
             base = 1.0
    else:
        base = 0.2
        
    # Add random fluctuation (Factory bursts, etc)
    noise = random.uniform(-0.1, 0.1)
    
    factor = max(0.0, base + noise)
    print(f"Urban Activity (Simulated): Hour {hour} -> Factor {factor:.2f}")
    return factor

def get_bio_factor():
    """Simulates Bio-Sensor (SNS Trends).
    In a real app, this would query Twitter API for '頭痛' (Headache) density.
    """
    # Simulate a "Collective Intuition"
    # Randomly returns high values to simulate a 'premonition'.
    # 90% chance of Low (0.0 - 0.2)
    # 10% chance of High (0.5 - 1.0) -> The "Bad Feeling"
    
    roll = random.random()
    if roll > 0.9:
        # High Anxiety / Headache trend
        factor = random.uniform(0.6, 1.0)
        print(f"Bio-Sensor (SNS): ALERT! High volume of 'Headache' reports. Factor {factor:.2f}")
    else:
        factor = random.uniform(0.0, 0.2)
        print(f"Bio-Sensor (SNS): Calm. Factor {factor:.2f}")
        
    return factor

if __name__ == "__main__":
    get_urban_factor()
    get_bio_factor()
