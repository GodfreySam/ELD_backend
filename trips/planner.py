from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Dict, List, Tuple

# City lookup with real coordinates for map rendering
CITY_TO_COORD: Dict[str, Tuple[float, float]] = {
    "Atlanta, GA": (33.7490, -84.3880),
    "Boston, MA": (42.3601, -71.0589),
    "Chicago, IL": (41.8781, -87.6298),
    "Dallas, TX": (32.7767, -96.7970),
    "Denver, CO": (39.7392, -104.9903),
    "Detroit, MI": (42.3314, -83.0458),
    "Houston, TX": (29.7604, -95.3698),
    "Kansas City, MO": (39.0997, -94.5786),
    "Las Vegas, NV": (36.1699, -115.1398),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Miami, FL": (25.7617, -80.1918),
    "Minneapolis, MN": (44.9778, -93.2650),
    "Nashville, TN": (36.1627, -86.7816),
    "New Orleans, LA": (29.9511, -90.0715),
    "New York, NY": (40.7128, -74.0060),
    "Philadelphia, PA": (39.9526, -75.1652),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Portland, OR": (45.5152, -122.6784),
    "San Antonio, TX": (29.4241, -98.4936),
    "San Diego, CA": (32.7157, -117.1611),
    "San Francisco, CA": (37.7749, -122.4194),
    "Seattle, WA": (47.6062, -122.3321),
    "St. Louis, MO": (38.6270, -90.1994),
    "Washington, DC": (38.9072, -77.0369),
}


def haversine_miles(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    R_km = 6371.0
    lat1, lon1 = a
    lat2, lon2 = b
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    lat1_r = radians(lat1)
    lat2_r = radians(lat2)
    h = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    c = 2 * asin(min(1.0, sqrt(h)))
    return (R_km * c) * 0.621371


@dataclass
class PlanOutput:
    polyline: List[Tuple[float, float]]
    distance_miles: float
    duration_hours: float
    stops: List[dict]
    logs: List[dict]


def plan_trip(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
    current_cycle_hours: float,
    start_date: date,
) -> PlanOutput:
    # Fallback: if unknown city, keep polyline empty
    start = CITY_TO_COORD.get(pickup_location)
    end = CITY_TO_COORD.get(dropoff_location)

    polyline: List[Tuple[float, float]] = []
    distance_miles = 0.0
    if start and end:
        polyline = [start, end]
        distance_miles = haversine_miles(start, end)

    # Simple average speed assumption
    average_mph = 55.0
    driving_hours_total = distance_miles / average_mph if distance_miles > 0 else 8.0

    # Hours-of-service: 70 hours in 8 days. Input is hours already used.
    cycle_hours_remaining = max(0.0, 70.0 - float(current_cycle_hours))

    # Add 1h for pickup and 1h for drop-off per scope (counted toward on-duty)
    # We will ensure per-day on-duty window does not exceed 14 hours.

    # Split across days respecting basic constraints: 11h driving/day, 14h on-duty window
    remaining_drive = driving_hours_total
    day_logs: List[dict] = []
    day = 0

    while remaining_drive > 0 or day == 0:
        if cycle_hours_remaining <= 0:
            # No on-duty hours left in cycle; insert a full off-duty reset day and stop planning further
            segments_reset = [{"startHour": 0, "endHour": 24.0, "lane": "off"}]
            day_logs.append({
                "date": (start_date + timedelta(days=day)).isoformat(),
                "segments": segments_reset,
            })
            break

        segments = []  # per-day segments
        # Day start with pickup only on first day
        if day == 0:
            pickup_on_duty = 1.0 if cycle_hours_remaining > 0 else 0.0
            if pickup_on_duty > 0:
                segments.append({"startHour": 0, "endHour": 1, "lane": "onduty"})
                cycle_hours_remaining = max(0.0, cycle_hours_remaining - pickup_on_duty)
            window_start = pickup_on_duty
        else:
            window_start = 0.0

        # Driving for the day (cap by 11-hour driving limit and remaining cycle hours)
        # Reserve up to 0.5h for a break if we might exceed 8 hours driving
        potential_drive_cap = 11.0
        # Remaining on-duty window for the day (14-hour window minus window_start)
        onduty_window_remaining = max(0.0, 14.0 - window_start)
        # If we will exceed 8h driving today, account for 0.5h break in on-duty window
        drive_today_raw = min(potential_drive_cap, remaining_drive if remaining_drive > 0 else 8.0)
        needs_break = drive_today_raw > 8.0
        onduty_overhead = 0.5 if needs_break else 0.0
        # Also consider last-day drop-off 1h if we can finish today; approximate check
        will_finish_today = drive_today_raw >= remaining_drive and remaining_drive > 0
        drop_off_overhead = 1.0 if will_finish_today else 0.0
        # On-duty available given cycle
        onduty_available_today = min(onduty_window_remaining, cycle_hours_remaining)
        # Max driving possible given on-duty available after overheads
        max_drive_by_window = max(0.0, onduty_available_today - onduty_overhead - drop_off_overhead)
        drive_today = max(0.0, min(drive_today_raw, max_drive_by_window))

        # 30-min break after 8 hours of driving within the day (if we exceed 8h)
        if drive_today > 8.0:
            # First 8h driving
            segments.append({"startHour": window_start, "endHour": window_start + 8.0, "lane": "driving"})
            # 0.5h break (on duty not driving)
            segments.append({"startHour": window_start + 8.0, "endHour": window_start + 8.5, "lane": "onduty"})
            # Remaining driving after break
            post_break_drive = drive_today - 8.0
            segments.append({"startHour": window_start + 8.5, "endHour": window_start + 8.5 + post_break_drive, "lane": "driving"})
            t = window_start + 8.5 + post_break_drive
        else:
            segments.append({"startHour": window_start, "endHour": window_start + drive_today, "lane": "driving"})
            t = window_start + drive_today

        # Deduct on-duty used (driving + any break this day)
        day_onduty_used = drive_today + (0.5 if drive_today > 8.0 else 0.0)
        cycle_hours_remaining = max(0.0, cycle_hours_remaining - day_onduty_used)
        remaining_drive = max(0.0, remaining_drive - drive_today)

        # If last day, add 1h drop-off, else off duty until 24h
        if remaining_drive <= 0 and cycle_hours_remaining > 0:
            drop = min(1.0, cycle_hours_remaining)
            segments.append({"startHour": t, "endHour": min(24.0, t + drop), "lane": "onduty"})
            t = min(24.0, t + drop)
            cycle_hours_remaining = max(0.0, cycle_hours_remaining - drop)

        # Off duty for the rest of the day
        if t < 24.0:
            segments.append({"startHour": t, "endHour": 24.0, "lane": "off"})

        day_logs.append({
            "date": (start_date + timedelta(days=day)).isoformat(),
            "segments": segments,
        })
        day += 1

        # 10h off-duty between days implicitly represented by the overnight off segment

        # Stop if we created at least one day and there was no distance
        if distance_miles == 0 and day >= 1:
            break

    # Approximate total service hours as driving plus assumed 1h pickup and 1h dropoff (if distance>0)
    service_hours_total = driving_hours_total + (2.0 if distance_miles > 0 else 0.0)
    duration_hours = service_hours_total

    # Simple stop list: fuel every ~1000 miles and a rest at 8h on first day
    stops: List[dict] = []
    if distance_miles > 0:
        miles = distance_miles
        i = 1000.0
        while i < miles:
            stops.append({"mile": i, "type": "fuel"})
            i += 1000.0
    stops.append({"hour": 8.0, "type": "rest"})

    return PlanOutput(
        polyline=polyline,
        distance_miles=round(distance_miles, 1),
        duration_hours=round(duration_hours, 1),
        stops=stops,
        logs=day_logs,
    )
