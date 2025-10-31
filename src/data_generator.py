
"""
data_generator.py
Generates synthetic traffic sensor data for the smart traffic control system
"""

import pandas as pd
import random
import os
from datetime import datetime, timedelta


class TrafficDataGenerator:
    """Generate synthetic traffic sensor data for intersections"""

    def __init__(self, num_intersections=20, hours=24):
        self.num_intersections = num_intersections
        self.hours = hours
        self.intersections = self._create_intersections()

    def _create_intersections(self):
        """Create intersection metadata"""
        intersections = []
        locations = [
            "Main St & 1st Ave", "Broadway & 5th Ave", "Park Ave & 10th St",
            "Ocean Blvd & Beach Rd", "Highway 101 & Exit 5", "Downtown Plaza",
            "Airport Rd & Terminal Way", "University Ave & College St",
            "Industrial Park Entrance", "Shopping Center Main Gate",
            "Residential Area A", "Residential Area B", "City Center North",
            "City Center South", "East Side Junction", "West Side Junction",
            "North Expressway Entry", "South Expressway Exit",
            "Metro Station Plaza", "Business District Hub"
        ]

        for i in range(self.num_intersections):
            intersections.append({
                "intersection_id": f"INT_{i+1:03d}",
                "location": locations[i] if i < len(locations) else f"Intersection {i+1}",
                "latitude": 40.7128 + random.uniform(-0.5, 0.5),
                "longitude": -74.0060 + random.uniform(-0.5, 0.5),
                "num_lanes": random.choice([2, 3, 4, 6]),
                "capacity_per_hour": random.randint(800, 2000),
            })
        return pd.DataFrame(intersections)

    def _generate_traffic_pattern(self, hour, is_weekend=False):
        """Generate realistic traffic patterns based on time of day"""
        # Peak hours: 7-9 AM and 5-7 PM on weekdays
        if not is_weekend:
            if 7 <= hour <= 9:
                return random.uniform(0.7, 0.95)  # Morning rush
            elif 17 <= hour <= 19:
                return random.uniform(0.75, 1.0)  # Evening rush
            elif 12 <= hour <= 14:
                return random.uniform(0.5, 0.7)  # Lunch time
            elif 22 <= hour or hour <= 5:
                return random.uniform(0.1, 0.3)  # Night time
            else:
                return random.uniform(0.4, 0.6)  # Normal hours
        else:
            # Weekend patterns
            if 10 <= hour <= 20:
                return random.uniform(0.4, 0.6)
            else:
                return random.uniform(0.2, 0.4)

    def generate_sensor_data(self, start_date=None, interval_minutes=5):
        """Generate time-series sensor data"""
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        data = []
        total_intervals = (self.hours * 60) // interval_minutes

        for intersection in self.intersections.to_dict("records"):
            for i in range(total_intervals):
                timestamp = start_date + timedelta(minutes=i * interval_minutes)
                hour = timestamp.hour
                is_weekend = timestamp.weekday() >= 5

                # Get traffic pattern multiplier
                pattern_multiplier = self._generate_traffic_pattern(hour, is_weekend)

                # Base vehicle count with pattern
                base_count = intersection["capacity_per_hour"] * pattern_multiplier
                vehicle_count = int(base_count * random.uniform(0.8, 1.2) / (60 / interval_minutes))

                # Speed inversely related to congestion
                congestion_ratio = vehicle_count / (intersection["capacity_per_hour"] / (60 / interval_minutes))
                if congestion_ratio < 0.3:
                    avg_speed = random.uniform(45, 55)
                elif congestion_ratio < 0.6:
                    avg_speed = random.uniform(30, 45)
                elif congestion_ratio < 0.8:
                    avg_speed = random.uniform(15, 30)
                else:
                    avg_speed = random.uniform(5, 15)

                data.append(
                    {
                        "timestamp": timestamp,
                        "intersection_id": intersection["intersection_id"],
                        "vehicle_count": vehicle_count,
                        "average_speed": round(avg_speed, 2),
                        "num_lanes": intersection["num_lanes"],
                    }
                )

        return pd.DataFrame(data)

    def save_to_csv(self, output_dir="data/raw"):
        """Generate and save data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)

        # Save intersection metadata
        metadata_path = os.path.join(output_dir, "intersection_metadata.csv")
        self.intersections.to_csv(metadata_path, index=False)

        # Generate sensor data
        sensor_data = self.generate_sensor_data()
        sensor_path = os.path.join(output_dir, "traffic_sensor_data.csv")
        sensor_data.to_csv(sensor_path, index=False)

        print(f"Saved intersection metadata to {metadata_path}")
        print(f"Saved sensor data to {sensor_path}")
        print(f"Generated {len(sensor_data)} sensor readings for {self.num_intersections} intersections")

        return metadata_path, sensor_path


if __name__ == "__main__":
    generator = TrafficDataGenerator(num_intersections=20, hours=24)
    metadata_path, sensor_path = generator.save_to_csv()

    print("\nData generation complete!")
    print(f"Total records: {len(pd.read_csv(sensor_path))}")
