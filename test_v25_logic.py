
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add path to Earthquake_PoC
sys.path.append(os.path.join(os.getcwd(), "Earthquake_PoC"))

import monitor

class TestV25RiskLogic(unittest.TestCase):
    
    @patch('monitor.fetch_space.get_solar_flux')
    @patch('monitor.fetch_aurora.get_aurora_data')
    @patch('monitor.fetch_nict.get_nict_data')
    @patch('monitor.fetch_jaxa.get_sar_status')
    @patch('monitor.fetch_earthquake.get_earthquake_history')
    @patch('monitor.fetch_earthquake.get_usgs_data')
    def test_zero_base_risk_plus_sar(self, mock_usgs, mock_hist, mock_jaxa, mock_nict, mock_aurora, mock_space):
        """
        Verify that even with 0 solar/ionosphere risk, 
        SAR detection adds +50 to the global modifier.
        """
        # 1. Setup Safe Environment (Base Risk ~ 0)
        mock_space.return_value = 0.0 # No solar
        mock_aurora.return_value = {"power_gw": 0, "damping_factor": 0}
        mock_nict.return_value = {"risk_score": 0, "ionosphere_level": 0}
        mock_hist.return_value = [] # No local quakes
        mock_usgs.return_value = [] # No global quakes
        
        # 2. SAR Detected
        mock_jaxa.return_value = {"detected": True, "risk_multiplier": 1.5, "source": "TEST"}
        
        # 3. Run Logic
        # generate_predictions_v23 returns a dict
        result = monitor.generate_predictions_v23(history_data=[], usgs_data=[])
        preds = result["predictions"]
        
        # 4. Assertions
        # Base Risk ~ 0
        # SAR Baseline = +20 (was +50, but updated to +20.0 fixed baseline in Task 2)
        # Probability = 30 + 20 = 50
        
        self.assertTrue(len(preds) > 0, "Should generate a Global Alert")
        alert = preds[0]
        # Depending on recent changes, check if the value is correct
        # monitor.py: global_modifier += int(net_solar_bonus + final_ionosphere_risk + structural_stress)
        # structural_stress is 20.0
        
        self.assertEqual(alert["probability"], 50, 
            f"Expected Probability 50 (30 base + 20 SAR), got {alert['probability']}")
            
        print("\n✅ Test Passed: SAR Detection correctly adds +20 baseline.")

    @patch('monitor.fetch_space.get_solar_flux')
    def test_solar_cancel_filter(self, mock_space):
        """Task 3A: Solar Noise Cancellation"""
        # Logic: Space > 3.0 -> Ionosphere * 0.2
        pass # To be implemented fully if needed, or integrated below
        
    @patch('monitor.fetch_space.get_solar_flux')
    @patch('monitor.fetch_aurora.get_aurora_data')
    @patch('monitor.fetch_nict.get_nict_data')
    @patch('monitor.fetch_jaxa.get_sar_status')
    @patch('monitor.fetch_earthquake.get_earthquake_history')
    @patch('monitor.fetch_earthquake.get_usgs_data')
    def test_solar_cancel_and_true_signal(self, mock_usgs, mock_hist, mock_jaxa, mock_nict, mock_aurora, mock_space):
        """
        Verify Task 3 Logic:
        Case A: High Solar (4.0) -> Suppress Ionosphere Risk
        Case B: Low Solar (1.0) + High Risk -> True Signal Boost
        """
        # --- Case A: Solar Noise ---
        mock_space.return_value = 4.0 # High Solar
        mock_aurora.return_value = {"power_gw": 0, "damping_factor": 0}
        mock_nict.return_value = {"risk_score": 10.0, "ionosphere_level": 3} # Max Risk
        mock_jaxa.return_value = {"detected": False, "source": "TEST"}
        mock_hist.return_value = []
        mock_usgs.return_value = []
        
        result = monitor.generate_predictions_v23(history_data=[], usgs_data=[])
        # Calculation:
        # Solar Bonus = 4.0 * 5 = 20
        # Ionosphere = 10.0 * 0.2 = 2.0 (Suppressed)
        # Total Mod = 20 + 2 = 22
        # Prob = 30 + 22 = 52
        
        preds = result["predictions"]
        self.assertEqual(len(preds), 1)
        self.assertEqual(preds[0]["probability"], 52)
        self.assertEqual(result["filter_status"], "Solar Cancelled")
        print("\n✅ Test Passed: Solar Noise Cancelled (Risk 10.0 -> 2.0).")
        
        # --- Case B: True Signal ---
        mock_space.return_value = 1.0 # Low Solar
        mock_nict.return_value = {"risk_score": 10.0, "ionosphere_level": 3}
        
        result = monitor.generate_predictions_v23(history_data=[], usgs_data=[])
        # Calculation:
        # Solar Bonus = 1.0 * 5 = 5
        # Ionosphere = 10.0 * 2.0 = 20.0 (Boosted)
        # Total Mod = 5 + 20 = 25
        # Prob = 30 + 25 = 55
        
        preds = result["predictions"]
        self.assertEqual(preds[0]["probability"], 55)
        self.assertEqual(result["filter_status"], "True Signal DETECTED")
        print("\n✅ Test Passed: True Signal Boosted (Risk 10.0 -> 20.0).")
        """
        Verify that Aurora Damping cancels out Solar Flux risk.
        """
        # 1. Setup High Solar but High Damping
        mock_space.return_value = 4.0 # High Solar -> 4 * 5 = 20 raw score
        mock_aurora.return_value = {"power_gw": 500, "damping_factor": 25.0} # Damping 25
        # Net Solar = max(0, 20 - 25) = 0
        
        mock_nict.return_value = {"risk_score": 0, "ionosphere_level": 0}
        mock_jaxa.return_value = {"detected": False, "source": "TEST"}
        mock_hist.return_value = []
        mock_usgs.return_value = []
        
        # 3. Run Logic
        result = monitor.generate_predictions_v23(history_data=[], usgs_data=[])
        preds = result["predictions"]
        
        # 4. Assertions
        # Should be NO alert because global_modifier = 0
        self.assertEqual(len(preds), 0, "Should have 0 alerts due to Aurora Damping")
        
        print("\n✅ Test Passed: Aurora Damping successfully neutralized Solar Risk.")

if __name__ == '__main__':
    unittest.main()
