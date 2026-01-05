import unittest
from modules.alert_engine import AlertEngine

class TestDroneSecurityAgent(unittest.TestCase):
    
    def setUp(self):
        self.alert_engine = AlertEngine()

    def test_alert_rule_person_restricted(self):
        # Test Rule 1: Person in Restricted Zone
        description = "A person is detected in the restricted area."
        
        alert = self.alert_engine.check_rules(description, "frame1.jpg")
        self.assertIsNotNone(alert)
        self.assertEqual(alert['severity'], "HIGH")
        self.assertEqual(alert['type'], "Security Breach")
        print(f"Alert Triggered: {alert}")

    def test_alert_rule_suspicious(self):
        # Test Rule 2: Suspicious Activity
        description = "Suspicious behavior detected in the area."
        
        alert = self.alert_engine.check_rules(description, "frame2.jpg")
        self.assertIsNotNone(alert)
        self.assertEqual(alert['severity'], "MEDIUM")
        print(f"Alert Triggered: {alert}")

    def test_alert_rule_weapon(self):
        # Test Rule 3: Weapon Detection
        description = "Armed individual with weapon detected."
        
        alert = self.alert_engine.check_rules(description, "frame3.jpg")
        self.assertIsNotNone(alert)
        self.assertEqual(alert['severity'], "CRITICAL")
        print(f"Alert Triggered: {alert}")

    def test_no_alert(self):
        # Test normal condition
        description = "A person walking normally in the area."
        
        alert = self.alert_engine.check_rules(description, "frame4.jpg")
        self.assertIsNone(alert)
        print("No alert triggered for normal condition.")

if __name__ == '__main__':
    unittest.main()
