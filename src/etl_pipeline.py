
"""
etl_pipeline.py
PySpark ETL Pipeline for processing traffic sensor data
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, sum as spark_sum, count, hour, when
from pyspark.sql.functions import round as spark_round
from pyspark.sql.types import TimestampType
import os
from typing import Optional


def compute_traffic_congestion_index(
    vehicle_count: float, average_speed: float, capacity_per_hour: float, interval_minutes: int = 5
) -> float:
    """Pure helper to compute the Traffic Congestion Index (TCI) for a single reading.

    This mirrors the logic used in the Spark transformation:
      - capacity_per_5min = capacity_per_hour / (60 / interval_minutes)
      - volume_ratio = vehicle_count / capacity_per_5min
      - speed_factor = 1 - (average_speed / 55.0)
      - tci = round(min(volume_ratio * speed_factor * 100, 100), 2)

    Returns 0.0 if capacity_per_hour is zero or invalid to avoid division errors.

    The function can return negative values if average_speed > 55 (keeps parity with Spark code).
    """
    try:
        if capacity_per_hour is None or capacity_per_hour <= 0:
            return 0.0

        intervals_per_hour = 60 // interval_minutes
        capacity_per_interval = capacity_per_hour / intervals_per_hour
        if capacity_per_interval == 0:
            return 0.0

        volume_ratio = float(vehicle_count) / float(capacity_per_interval)
        speed_factor = 1.0 - (float(average_speed) / 55.0)

        raw = volume_ratio * speed_factor * 100.0
        tci = min(raw, 100.0)
        return round(tci, 2)
    except Exception:
        return 0.0


class TrafficETLPipeline:
    """ETL Pipeline for traffic data processing using PySpark"""

    def __init__(self, app_name="TrafficETL"):
        self.spark = self._create_spark_session(app_name)

    def _create_spark_session(self, app_name):
        """Create and configure Spark session"""
        return (
            SparkSession.builder.appName(app_name)
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .getOrCreate()
        )

    def extract(self, sensor_data_path, metadata_path):
        """Extract data from CSV files"""
        print(f"Extracting data from {sensor_data_path} and {metadata_path}")

        sensor_df = self.spark.read.csv(sensor_data_path, header=True, inferSchema=True)
        metadata_df = self.spark.read.csv(metadata_path, header=True, inferSchema=True)

        print(f"Extracted {sensor_df.count()} sensor records")
        print(f"Extracted {metadata_df.count()} intersection records")

        return sensor_df, metadata_df

    def transform(self, sensor_df, metadata_df):
        """Transform and enrich traffic data"""
        print("Starting transformation...")

        sensor_df = sensor_df.withColumn("timestamp", col("timestamp").cast(TimestampType()))

        # Join sensor data with metadata. Use explicit column selection to avoid ambiguous
        # column references when both sides contain the same column names (e.g., num_lanes).
        s = sensor_df.alias("s")
        m = metadata_df.alias("m")

        enriched_df = s.join(m, on="intersection_id", how="left").select(
            col("s.timestamp").alias("timestamp"),
            col("s.intersection_id").alias("intersection_id"),
            col("s.vehicle_count").alias("vehicle_count"),
            col("s.average_speed").alias("average_speed"),
            # prefer metadata num_lanes if available, fall back to sensor value
            when(col("m.num_lanes").isNotNull(), col("m.num_lanes")).otherwise(col("s.num_lanes")).alias("num_lanes"),
            col("m.location").alias("location"),
            col("m.latitude").alias("latitude"),
            col("m.longitude").alias("longitude"),
            col("m.capacity_per_hour").alias("capacity_per_hour"),
        )

        enriched_df = enriched_df.withColumn("capacity_per_5min", col("capacity_per_hour") / 12)
        enriched_df = enriched_df.withColumn("volume_ratio", col("vehicle_count") / col("capacity_per_5min"))
        enriched_df = enriched_df.withColumn("speed_factor", 1 - (col("average_speed") / 55.0))

        enriched_df = enriched_df.withColumn(
            "traffic_congestion_index",
            spark_round(
                when(col("volume_ratio") * col("speed_factor") * 100 > 100, 100).otherwise(
                    col("volume_ratio") * col("speed_factor") * 100
                ),
                2,
            ),
        )

        enriched_df = enriched_df.withColumn("hour", hour("timestamp"))
        enriched_df = enriched_df.withColumn(
            "time_of_day",
            when((col("hour") >= 6) & (col("hour") < 12), "Morning")
            .when((col("hour") >= 12) & (col("hour") < 18), "Afternoon")
            .when((col("hour") >= 18) & (col("hour") < 22), "Evening")
            .otherwise("Night"),
        )

        enriched_df = enriched_df.withColumn(
            "congestion_level",
            when(col("traffic_congestion_index") < 20, "Low")
            .when(col("traffic_congestion_index") < 40, "Moderate")
            .when(col("traffic_congestion_index") < 60, "High")
            .when(col("traffic_congestion_index") < 80, "Severe")
            .otherwise("Critical"),
        )

        print(f"Transformation complete. Total records: {enriched_df.count()}")

        return enriched_df

    def aggregate_metrics(self, enriched_df):
        """Create aggregated metrics for dashboard"""
        print("Creating aggregated metrics...")

        hourly_metrics = (
            enriched_df.groupBy("intersection_id", "location", "hour")
            .agg(
                spark_sum("vehicle_count").alias("total_vehicles"),
                avg("average_speed").alias("avg_speed"),
                avg("traffic_congestion_index").alias("avg_congestion_index"),
                count("*").alias("reading_count"),
            )
            .orderBy("intersection_id", "hour")
        )

        intersection_stats = (
            enriched_df.groupBy(
                "intersection_id",
                "location",
                "latitude",
                "longitude",
                "num_lanes",
                "capacity_per_hour",
            )
            .agg(
                avg("vehicle_count").alias("avg_vehicle_count"),
                avg("average_speed").alias("avg_speed"),
                avg("traffic_congestion_index").alias("avg_congestion_index"),
            )
            .orderBy(col("avg_congestion_index").desc())
        )

        return hourly_metrics, intersection_stats

    def load(self, df, output_path, file_format="parquet"):
        """Load processed data to storage"""
        print(f"Loading data to {output_path}")

        os.makedirs(output_path, exist_ok=True)

        if file_format == "parquet":
            df.write.mode("overwrite").parquet(output_path)
        elif file_format == "csv":
            df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_path)

        print(f"Data successfully loaded to {output_path}")

    def run_pipeline(self, sensor_data_path, metadata_path, output_base_path="data/processed"):
        """Execute the complete ETL pipeline"""
        print("=" * 60)
        print("Starting Traffic ETL Pipeline")
        print("=" * 60)

        sensor_df, metadata_df = self.extract(sensor_data_path, metadata_path)
        enriched_df = self.transform(sensor_df, metadata_df)
        hourly_metrics, intersection_stats = self.aggregate_metrics(enriched_df)

        self.load(enriched_df, f"{output_base_path}/enriched_data", "parquet")
        self.load(hourly_metrics, f"{output_base_path}/hourly_metrics", "parquet")
        self.load(intersection_stats, f"{output_base_path}/intersection_stats", "parquet")

        self.load(enriched_df, f"{output_base_path}/enriched_data_csv", "csv")
        self.load(hourly_metrics, f"{output_base_path}/hourly_metrics_csv", "csv")
        self.load(intersection_stats, f"{output_base_path}/intersection_stats_csv", "csv")

        print("=" * 60)
        print("ETL Pipeline Complete!")
        print("=" * 60)

        return enriched_df, hourly_metrics, intersection_stats

    def stop(self):
        """Stop Spark session"""
        self.spark.stop()


if __name__ == "__main__":
    pipeline = TrafficETLPipeline()

    sensor_data_path = "data/raw/traffic_sensor_data.csv"
    metadata_path = "data/raw/intersection_metadata.csv"

    enriched_df, hourly_metrics, intersection_stats = pipeline.run_pipeline(
        sensor_data_path, metadata_path
    )

    print("\nSample Enriched Data:")
    enriched_df.show(5)

    print("\nTop 5 Most Congested Intersections:")
    intersection_stats.show(5)

    pipeline.stop()
