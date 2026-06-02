"""
Centralized configuration for Trackflation project.
Includes real-world records, biological ceilings, and simulation parameters.
"""

# Real World Records as of June 2026
REAL_WR_2026 = {
    "100m": 9.58,
    "200m": 19.19,
    "400m": 43.03,
    "800m": 100.91,      # 1:40.91
    "1500m": 206.00,     # 3:26.00
    "5000m": 755.36,     # 12:35.36
    "10000m": 1571.00,   # 26:11.00
    "Marathon": 7170.00, # 1:59:30
    "Steeplechase": 472.11 # 7:52.11
}

# Physical Floors (Caps) for tapering logistic growth
# Based on biomechanical and physiological limits
BIOLOGICAL_FLOORS = {
    "100m": 9.45,
    "200m": 18.90,
    "400m": 42.50,
    "800m": 99.50,       # 1:39.50
    "1500m": 204.00,     # 3:24.00
    "5000m": 745.00,     # 12:25.00
    "10000m": 1550.00,   # 25:50.00
    "Marathon": 7020.00, # 1:57:00
    "Steeplechase": 465.00 # 7:45.00
}

# Event Metadata for Simulation/Visualization
EVENT_METADATA = {
    "100m": {"code": "100-metres", "base": 10.15, "rate": 0.012, "is_sprint": True},
    "200m": {"code": "200-metres", "base": 20.30, "rate": 0.022, "is_sprint": True},
    "400m": {"code": "400-metres", "base": 44.60, "rate": 0.035, "is_sprint": False},
    "800m": {"code": "800-metres", "base": 105.5, "rate": 0.09, "is_sprint": False},
    "1500m": {"code": "1500-metres", "base": 216.0, "rate": 0.20, "is_sprint": False},
    "5000m": {"code": "5000-metres", "base": 805.0, "rate": 0.95, "is_sprint": False},
    "10000m": {"code": "10000-metres", "base": 1665.0, "rate": 1.80, "is_sprint": False},
    "Marathon": {"code": "marathon", "base": 7700.0, "rate": 10.0, "is_sprint": False},
    "Steeplechase": {"code": "3000-metres-steeplechase", "base": 500.0, "rate": 0.55, "is_sprint": False}
}

# Global Settings
START_YEAR = 1974
END_YEAR = 2026
PROJECTION_YEARS = 20 # Forecast to 2046
ALPHA = 0.05 # For 95% Conformal Intervals
