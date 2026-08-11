"""
Centralized configuration for the Trackflation project.

Scope: every figure here is for **men's senior outdoor** events only. Nothing in
this project analyses women's events; do not reuse these constants for them.
"""

# ---------------------------------------------------------------- World records
#
# Men's senior outdoor world records. Each entry cites the performance it comes
# from so it can be re-checked; the canonical list is
# https://worldathletics.org/records/by-category/world-records
# and every mark below also sits at rank 1 of the corresponding World Athletics
# all-time toplist (https://worldathletics.org/records/toplists/...alltime),
# which is what `scripts/verify_world_records.py` re-checks against.
#
# Verified against the World Athletics all-time toplists on 2026-08-11.
REAL_WR = {
    "100m": 9.58,        # 9.58    Usain Bolt (JAM), Berlin, 16 Aug 2009
    "200m": 19.19,       # 19.19   Usain Bolt (JAM), Berlin, 20 Aug 2009
    "400m": 43.03,       # 43.03   Wayde van Niekerk (RSA), Rio de Janeiro, 14 Aug 2016
    "800m": 100.91,      # 1:40.91 David Rudisha (KEN), London, 9 Aug 2012
    "1500m": 206.00,     # 3:26.00 Hicham El Guerrouj (MAR), Rome, 14 Jul 1998
    "5000m": 755.36,     # 12:35.36 Joshua Cheptegei (UGA), Monaco, 14 Aug 2020
    "10000m": 1571.00,   # 26:11.00 Joshua Cheptegei (UGA), Valencia, 7 Oct 2020
    "Marathon": 7170.00, # 1:59:30 Sabastian Sawe (KEN), London, 26 Apr 2026
    "Steeplechase": 472.11,  # 7:52.11 Lamecha Girma (ETH), Paris, 9 Jun 2023
}

# Backwards-compatible alias. The old name implied the values were pinned to a
# single season; they are simply the current records.
REAL_WR_2026 = REAL_WR

# ------------------------------------------------------- Assumed biological floors
#
# NOT measurements. These are the project's *assumed* asymptotes for the tapering
# logistic forecast, chosen as round numbers a little below the current record.
# They are an input to the projection, not a result of it -- a forecast fitted with
# a logistic floor cannot ever cross that floor, so any "we are approaching the
# ceiling" reading is a restatement of these numbers. `TrackForecaster` therefore
# reports a linear (floor-free) fit alongside the logistic one for comparison.
BIOLOGICAL_FLOORS = {
    "100m": 9.45,
    "200m": 18.90,
    "400m": 42.50,
    "800m": 99.50,       # 1:39.50
    "1500m": 204.00,     # 3:24.00
    "5000m": 745.00,     # 12:25.00
    "10000m": 1550.00,   # 25:50.00
    "Marathon": 7020.00, # 1:57:00
    "Steeplechase": 465.00,  # 7:45.00
}

# ------------------------------------------------------------- Event metadata
#
# `code` is the World Athletics URL slug; `is_sprint` marks the events where the
# +2.0 m/s wind rule applies (it is meaningless for 5000m and longer, and for
# road races, which are not wind-assisted-legal in the same sense).
EVENT_METADATA = {
    "100m": {"code": "100-metres", "is_sprint": True},
    "200m": {"code": "200-metres", "is_sprint": True},
    "400m": {"code": "400-metres", "is_sprint": False},
    "800m": {"code": "800-metres", "is_sprint": False},
    "1500m": {"code": "1500-metres", "is_sprint": False},
    "5000m": {"code": "5000-metres", "is_sprint": False},
    "10000m": {"code": "10000-metres", "is_sprint": False},
    "Marathon": {"code": "marathon", "is_sprint": False},
    "Steeplechase": {"code": "3000-metres-steeplechase", "is_sprint": False},
}

# World Athletics groups disciplines into these URL segments.
DISCIPLINE_GROUPS = {
    "100m": "sprints",
    "200m": "sprints",
    "400m": "sprints",
    "800m": "middlelong",
    "1500m": "middlelong",
    "5000m": "middlelong",
    "10000m": "middlelong",
    "Marathon": "road-running",
    "Steeplechase": "middlelong",
}

# ------------------------------------------------------------- Global settings

# World Athletics season toplists begin in 2001. Earlier seasons simply do not
# exist in the source, so this is the real start of the observable record.
START_YEAR = 2001
END_YEAR = 2026

PROJECTION_TARGET_YEAR = 2046  # Forecast horizon; periods are derived from this.
ALPHA = 0.05  # For 95% split-conformal intervals.

# The carbon-plate "super shoe" intervention. Nike's Vaporfly 4% went on general
# sale in mid-2017, so 2017 is the first fully-treated season.
SHOE_INTERVENTION_YEAR = 2017
