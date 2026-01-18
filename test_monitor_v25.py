
import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Ensure Earthquake_PoC is in path
sys.path.append(os.path.join(os.getcwd(), "Earthquake_PoC"))

import monitor_v25

class TestMonitorV25(unittest.TestCase):
    
    def setUp(self):
        # Reset cache
        if os.path.exists("v25_metrics_cache.json"):
            os.remove("v25_metrics_cache.json")
            
    def tearDown(self):
        if os.path.exists("v25_metrics_cache.json"):
            os.remove("v25_metrics_cache.json")

    @patch('monitor_v25.fetch_space.get_solar_flux')
    @patch('monitor_v25.fetch_aurora.get_aurora_data')
    @patch('monitor_v25.fetch_nict.get_nict_data')
    @patch('monitor_v25.fetch_jaxa.get_sar_status')
    @patch('monitor_v25.fetch_earthquake.get_earthquake_history')
    def test_trend_arrows(self, mock_hist, mock_jaxa, mock_nict, mock_aurora, mock_space):
        """Test if trend arrows change correctly across runs."""
        
        # Run 1: Initial Values
        mock_space.return_value = 1.0
        mock_aurora.return_value = {"damping_factor": 10.0}
        mock_nict.return_value = {"risk_score": 5.0} # Stable
        mock_jaxa.return_value = {"detected": False}
        mock_hist.return_value = []
        
        mon = monitor_v25.V25Monitor()
        res1 = mon.run()
        
        # Schema Check: status.solar.trend
        self.assertIn("→", res1["status"]["solar"]["trend"])
        self.assertEqual(res1["status"]["solar"]["class"], "B-Class (Weak)") # 1.0 < 1.5
        
        # Run 2: Space Factor RISES (1.0 -> 2.0, delta +1.0 > 0.1)
        mock_space.return_value = 2.0 
        
        mon = monitor_v25.V25Monitor() # Reloads cache
        res2 = mon.run()
        
        self.assertIn("↗", res2["status"]["solar"]["trend"], "Should show Rise arrow")
        self.assertEqual(res2["status"]["solar"]["class"], "C-Class (Moderate)") # 2.0 < 3.0
        
        # Run 3: Space Factor DROPS (2.0 -> 1.5, delta -0.5 < -0.1)
        mock_space.return_value = 1.5
        
        mon = monitor_v25.V25Monitor()
        res3 = mon.run()
        
        self.assertIn("↘", res3["status"]["solar"]["trend"], "Should show Drop arrow")
        
        print("\n✅ Test Passed: Trend Arrows & Solar Class working.")

    @patch('monitor_v25.fetch_space.get_solar_flux')
    @patch('monitor_v25.fetch_aurora.get_aurora_data')
    @patch('monitor_v25.fetch_nict.get_nict_data')
    @patch('monitor_v25.fetch_jaxa.get_sar_status')
    @patch('monitor_v25.fetch_earthquake.get_earthquake_history')
    def test_risk_logic_integration(self, mock_hist, mock_jaxa, mock_nict, mock_aurora, mock_space):
        """Test Stacking Logic + Solar Filter + New Schema"""
        # Case: Quiet Sun (1.0) + High Iono (6.0) + SAR (True)
        # 1. Base Risk = 0
        # 2. Structural = 20.0
        # 3. Solar Bonus = 0 (1.0*5 - 10 < 0)
        # 4. Iono = 6.0 * 2.0 (True Signal Boost) = 12.0
        # Total = 20 + 12 = 32
        
        mock_space.return_value = 1.0
        mock_aurora.return_value = {"damping_factor": 10.0} # Effectively 0 solar bonus
        mock_nict.return_value = {"risk_score": 6.0}
        mock_jaxa.return_value = {"detected": True}
        mock_hist.return_value = []
        
        mon = monitor_v25.V25Monitor()
        res = mon.run()
        
        gm = res["risk_metrics"]["total_score"]
        self.assertEqual(gm, 32, f"Expected Total Score 32, got {gm}")
        
        self.assertEqual(res["status"]["ionosphere"]["condition"], "True Signal")
        self.assertEqual(res["risk_metrics"]["structural"], 20.0)
        self.assertEqual(res["alert_level"], "CAUTION") # 30 <= 32 < 50
        
        print("\n✅ Test Passed: Integrated Risk Logic (SAR+SignalBoost) = 32 (CAUTION).")

if __name__ == '__main__':
    unittest.main()
