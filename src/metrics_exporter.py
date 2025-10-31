
"""
metrics_exporter.py
Export traffic metrics in Prometheus format for Grafana
"""

from prometheus_client import start_http_server, Gauge, CollectorRegistry
import pandas as pd
import time
import glob
import os


class TrafficMetricsExporter:
    """Export processed traffic metrics for Prometheus/Grafana"""

    def __init__(self, data_path="data/processed", port=8000):
        self.data_path = data_path
        self.port = port
        self.registry = CollectorRegistry()
        self._setup_metrics()

    def _setup_metrics(self):
        """Define Prometheus metrics"""
        self.vehicle_count_gauge = Gauge(
            "traffic_vehicle_count",
            "Current vehicle count at intersection",
            ["intersection_id", "location"],
            registry=self.registry,
        )

        self.avg_speed_gauge = Gauge(
            "traffic_average_speed",
            "Average speed at intersection (mph)",
            ["intersection_id", "location"],
            registry=self.registry,
        )

        self.congestion_index_gauge = Gauge(
            "traffic_congestion_index",
            "Traffic Congestion Index (0-100)",
            ["intersection_id", "location"],
            registry=self.registry,
        )

        self.congestion_level_gauge = Gauge(
            "traffic_congestion_level",
            "Congestion level (0=Low, 1=Moderate, 2=High, 3=Severe, 4=Critical)",
            ["intersection_id", "location"],
            registry=self.registry,
        )

    def _read_latest_csv(self, pattern):
        """Read the latest CSV file matching the pattern"""
        files = glob.glob(os.path.join(self.data_path, pattern))
        if not files:
            return None

        latest_file = max(files, key=os.path.getctime)
        return pd.read_csv(latest_file)

    def _congestion_level_to_numeric(self, level):
        """Convert congestion level string to numeric value"""
        levels = {"Low": 0, "Moderate": 1, "High": 2, "Severe": 3, "Critical": 4}
        return levels.get(level, 0)

    def update_metrics(self):
        """Update Prometheus metrics from processed data"""
        try:
            stats_df = self._read_latest_csv("intersection_stats_csv/*.csv")

            if stats_df is None:
                print("No data files found. Waiting for ETL pipeline to generate data...")
                return

            for _, row in stats_df.iterrows():
                intersection_id = row["intersection_id"]
                location = row["location"]

                self.vehicle_count_gauge.labels(intersection_id=intersection_id, location=location).set(
                    row.get("avg_vehicle_count", 0)
                )

                self.avg_speed_gauge.labels(intersection_id=intersection_id, location=location).set(
                    row.get("avg_speed", 0)
                )

                self.congestion_index_gauge.labels(intersection_id=intersection_id, location=location).set(
                    row.get("avg_congestion_index", 0)
                )

            print(f"Metrics updated at {time.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"Error updating metrics: {e}")

    def start(self, update_interval=30):
        """Start the metrics exporter server"""
        start_http_server(self.port, registry=self.registry)
        print(f"Metrics server started on port {self.port}")
        print(f"Access metrics at: http://localhost:{self.port}/metrics")
        print(f"Update interval: {update_interval} seconds")

        while True:
            self.update_metrics()
            time.sleep(update_interval)


if __name__ == "__main__":
    exporter = TrafficMetricsExporter(port=8000)
    exporter.start(update_interval=30)
