import logging
from typing import Dict, Any, Optional

class AlertEngine:
    """Evaluates security rules based on AI analysis."""
    def __init__(self):
        self.alerts = []
        
    def check_rules(self, description: str, frame_name: str) -> Optional[Dict[str, Any]]:
        """Checks predefined rules and returns an alert if triggered."""
        desc_lower = description.lower()
        
        alert = None
        
        # Rule 1: Person in Restricted Zone
        if "person" in desc_lower and "restricted" in desc_lower:
            alert = {
                "severity": "HIGH",
                "type": "Security Breach",
                "message": "Person detected in restricted area",
                "frame": frame_name
            }
            
        # Rule 2: Suspicious Activity Detection
        elif "suspicious" in desc_lower or "suspicious behavior" in desc_lower:
            alert = {
                "severity": "MEDIUM",
                "type": "Suspicious Activity",
                "message": "Suspicious activity detected",
                "frame": frame_name
            }
                
        # Rule 3: Weapon detection (keyword based)
        elif "weapon" in desc_lower or "gun" in desc_lower or "armed" in desc_lower:
            alert = {
                "severity": "CRITICAL",
                "type": "Weapon Detected",
                "message": "Potential weapon detected",
                "frame": frame_name
            }
        
        # Rule 4: Unauthorized Access
        elif "trespassing" in desc_lower or "unauthorized" in desc_lower or "intrusion" in desc_lower:
            alert = {
                "severity": "HIGH",
                "type": "Unauthorized Access",
                "message": "Unauthorized access detected",
                "frame": frame_name
            }
            
        if alert:
            self.alerts.append(alert)
            logging.warning(f"ALERT TRIGGERED: {alert['message']}")
            
            return alert
        return None
