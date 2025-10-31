import pytest

from src.etl_pipeline import compute_traffic_congestion_index


def test_tci_happy_path():
    # Typical values: vehicle count less than capacity -> moderate TCI
    tci = compute_traffic_congestion_index(vehicle_count=50, average_speed=30, capacity_per_hour=1200, interval_minutes=5)
    assert isinstance(tci, float)
    # Should be within 0-100
    assert 0.0 <= tci <= 100.0


def test_tci_zero_capacity():
    # If capacity is zero, function should return 0.0 and not raise
    tci = compute_traffic_congestion_index(vehicle_count=10, average_speed=20, capacity_per_hour=0, interval_minutes=5)
    assert tci == 0.0


def test_tci_high_vehicle_count_caps_at_100():
    # Extremely high vehicle count should cap the TCI at 100
    tci = compute_traffic_congestion_index(vehicle_count=10000, average_speed=5, capacity_per_hour=800, interval_minutes=5)
    assert tci == 100.0


def test_tci_high_speed_may_reduce_or_negative():
    # Very high speeds (above 55) produce negative speed_factor in the current formula
    tci = compute_traffic_congestion_index(vehicle_count=10, average_speed=80, capacity_per_hour=1200, interval_minutes=5)
    assert isinstance(tci, float)
