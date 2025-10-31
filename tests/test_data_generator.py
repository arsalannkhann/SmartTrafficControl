import os
import sys
import pytest
import pandas as pd

# Ensure project root is importable for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.data_generator import TrafficDataGenerator


def test_generate_sensor_data_basic():
    gen = TrafficDataGenerator(num_intersections=2, hours=1)
    df = gen.generate_sensor_data(interval_minutes=15)

    # basic sanity checks
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    expected_cols = {"timestamp", "intersection_id", "vehicle_count", "average_speed", "num_lanes"}
    assert expected_cols.issubset(set(df.columns))


def test_save_to_csv_creates_files(tmp_path):
    gen = TrafficDataGenerator(num_intersections=1, hours=1)
    outdir = tmp_path / "data" / "raw"
    outdir = str(outdir)
    metadata_path, sensor_path = gen.save_to_csv(output_dir=outdir)

    assert metadata_path is not None
    assert sensor_path is not None
    assert os.path.exists(metadata_path)
    assert os.path.exists(sensor_path)
