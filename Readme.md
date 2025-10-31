
# Generate README.md content
readme_content = """# 🚦 Smart Traffic Control System

A comprehensive, data-driven traffic management system that uses **PySpark ETL pipelines**, **Grafana dashboards**, and **Google Gemini AI** to optimize traffic light timings and reduce congestion.

## 🎯 Project Overview

This project implements a scalable smart traffic control system that:
- Generates realistic synthetic traffic sensor data
- Processes massive traffic data using PySpark ETL pipelines
- Calculates Traffic Congestion Index for each intersection
- Visualizes real-time metrics in Grafana dashboards
- Provides AI-driven traffic light timing recommendations using Google Gemini

## 🏗️ Architecture

```
┌─────────────────────┐
│  Data Generator     │ → Synthetic traffic sensor data
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PySpark ETL        │ → Extract, Transform, Load
│  - Extract CSV      │
│  - Calculate TCI    │
│  - Aggregate metrics│
└──────────┬──────────┘
           │
           ├─────────────────────┬──────────────────┐
           ▼                     ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Processed Data   │  │ Metrics Exporter │  │  Gradio UI       │
│ (Parquet/CSV)    │  │ (Prometheus)     │  │  + Gemini AI     │
└──────────────────┘  └────────┬─────────┘  └──────────────────┘
                               ▼
                      ┌──────────────────┐
                      │ Grafana Dashboard│
                      │ (Visualization)  │
                      └──────────────────┘
```

## 📋 Features

### 1. **Data Generation**
- Realistic traffic patterns with peak hours (7-9 AM, 5-7 PM)
- Multiple intersections with varying capacities
- Time-series sensor data (vehicle counts, speeds)

### 2. **PySpark ETL Pipeline**
- Extract: Ingest large CSV datasets
- Transform: 
  - Join sensor data with intersection metadata
  - Calculate Traffic Congestion Index (TCI)
  - Enrich with time-based features
  - Categorize congestion levels
- Load: Store as Parquet and CSV files

### 3. **Traffic Congestion Index (TCI)**
Formula: `TCI = (volume_ratio × speed_factor) × 100`
- `volume_ratio = vehicle_count / capacity`
- `speed_factor = 1 - (current_speed / free_flow_speed)`
- Range: 0-100 (higher = more congested)

### 4. **Grafana Dashboard**
- Real-time metrics visualization
- Time-series graphs showing TCI over 24 hours
- Intersection-level statistics
- Congestion heatmaps

### 5. **Gradio UI with Gemini AI**
- Interactive web interface
- Select any intersection
- Get AI-generated traffic light timing recommendations
- Detailed justifications based on real data

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- Java 11+ (required for PySpark)
- Grafana (for dashboard visualization)

### Step 1: Clone and Install Dependencies

```bash
# Create project directory
mkdir traffic_control_system
cd traffic_control_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your Gemini API key
# Get key from: https://makersuite.google.com/app/apikey
nano .env  # or use any text editor
```

### Step 3: Generate Traffic Data

```bash
python src/data_generator.py
```

This creates:
- `data/raw/traffic_sensor_data.csv` - Time-series sensor readings
- `data/raw/intersection_metadata.csv` - Intersection details

### Step 4: Run ETL Pipeline

```bash
python src/etl_pipeline.py
```

This processes data and creates:
- `data/processed/enriched_data/` - Parquet files with TCI calculations
- `data/processed/hourly_metrics/` - Hourly aggregations
- `data/processed/intersection_stats/` - Overall statistics
- CSV exports for Grafana

### Step 5: Start Metrics Exporter (Optional)

```bash
# In a new terminal
python src/metrics_exporter.py
```

Access Prometheus metrics at: http://localhost:8000/metrics

### Step 6: Setup Grafana Dashboard

#### Install Grafana

**On Ubuntu/Debian:**
```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
sudo systemctl start grafana-server
```

**On Windows/macOS:**
Download from: https://grafana.com/grafana/download

#### Configure Grafana

1. Open Grafana: http://localhost:3000
2. Login: admin/admin (change password on first login)
3. Add Data Source:
   - Click "Configuration" → "Data Sources"
   - Click "Add data source"
   - Select "CSV" or configure Prometheus (http://localhost:8000)
   - For CSV: Point to `data/processed/*_csv/` directories

4. Create Dashboard:
   - Click "+" → "Dashboard"
   - Add panels for:
     - Time-series: TCI over 24 hours
     - Gauge: Current congestion levels
     - Table: Intersection statistics
     - Bar chart: Vehicle counts by intersection

### Step 7: Launch Gradio UI

```bash
python src/gradio_ui.py
```

Access UI at: http://localhost:7860

## 📊 Usage Examples

### Generate Data for Different Scenarios

```python
from src.data_generator import TrafficDataGenerator

# Generate data for more intersections
generator = TrafficDataGenerator(num_intersections=50, hours=48)
generator.save_to_csv()
```

### Run ETL Pipeline Programmatically

```python
from src.etl_pipeline import TrafficETLPipeline

pipeline = TrafficETLPipeline()
enriched_df, hourly_metrics, intersection_stats = pipeline.run_pipeline(
    sensor_data_path="data/raw/traffic_sensor_data.csv",
    metadata_path="data/raw/intersection_metadata.csv"
)

# Analyze results
print(intersection_stats.show())
```

### Query Processed Data

```python
import pandas as pd

# Read processed data
enriched = pd.read_csv("data/processed/enriched_data_csv/*.csv")

# Find peak congestion times
peak_congestion = enriched.groupby('hour')['traffic_congestion_index'].mean()
print(peak_congestion.sort_values(ascending=False).head())
```

## 🎨 Grafana Dashboard Configuration

### Sample Panel Queries

**For CSV Data Source:**
- File path: `data/processed/hourly_metrics_csv/*.csv`
- Time field: `hour`
- Value field: `avg_congestion_index`

**For Prometheus Data Source:**
- Metric: `traffic_congestion_index`
- Query: `traffic_congestion_index{intersection_id="INT_001"}`

### Recommended Visualizations

1. **Time Series Graph** - TCI over 24 hours
2. **Stat Panels** - Current vehicle count, avg speed
3. **Gauge** - Real-time congestion level
4. **Bar Chart** - Congestion by intersection
5. **Table** - Detailed intersection statistics

## 🧪 Testing

### Verify Data Generation
```bash
python -c "import pandas as pd; print(pd.read_csv('data/raw/traffic_sensor_data.csv').head())"
```

### Verify ETL Processing
```bash
python -c "import pandas as pd; print(pd.read_csv('data/processed/intersection_stats_csv/*.csv').head())"
```

### Test Gemini Integration
```bash
# Ensure GEMINI_API_KEY is set in .env
python src/gradio_ui.py
# Open http://localhost:7860 and test an intersection
```

## 📈 Traffic Congestion Index (TCI) Calculation

The TCI is calculated using the formula:

```
TCI = min(100, (V/C) × (1 - S/S_max) × 100)

Where:
- V = Vehicle count in interval
- C = Road capacity for interval
- S = Average speed
- S_max = Free-flow speed (55 mph)
```

**Congestion Levels:**
- **Low:** TCI < 20
- **Moderate:** 20 ≤ TCI < 40
- **High:** 40 ≤ TCI < 60
- **Severe:** 60 ≤ TCI < 80
- **Critical:** TCI ≥ 80

## 🤖 AI Decision Logic

The Gemini AI analyzes:
1. Current traffic metrics (vehicle count, speed, TCI)
2. Historical patterns (24-hour averages, peak hours)
3. Intersection characteristics (capacity, lanes)

And provides:
- Recommended signal timing
- Detailed justification referencing specific metrics
- Optimization suggestions

## 🔧 Troubleshooting

### PySpark Issues
```bash
# Ensure Java is installed
java -version

# If PySpark fails, try setting JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

### Grafana Not Connecting
- Check that data files exist in `data/processed/*_csv/`
- Verify CSV data source path is correct
- Ensure Grafana has read permissions

### Gemini API Errors
```bash
# Verify API key is set
echo $GEMINI_API_KEY  # Linux/Mac
echo %GEMINI_API_KEY%  # Windows

# Test API key
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('Success')"
```

### No Data in Gradio UI
Ensure you've run the ETL pipeline:
```bash
python src/etl_pipeline.py
```

## 📁 Project Structure

```
traffic_control_system/
│
├── data/
│   ├── raw/                          # Raw traffic sensor data
│   │   ├── traffic_sensor_data.csv
│   │   └── intersection_metadata.csv
│   └── processed/                    # Processed parquet/CSV files
│       ├── enriched_data/
│       ├── hourly_metrics/
│       └── intersection_stats/
│
├── src/
│   ├── __init__.py
│   ├── data_generator.py            # Generate synthetic traffic data
│   ├── etl_pipeline.py              # PySpark ETL pipeline
│   ├── metrics_exporter.py          # Export metrics for Grafana
│   └── gradio_ui.py                 # Gradio UI with Gemini integration
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                            # Your API keys (gitignored)
└── README.md                       # This file
```

## 🔐 Security Notes

- Never commit `.env` file with real API keys
- Use `.gitignore` to exclude sensitive files
- Rotate API keys regularly
- Limit API key permissions where possible

## 🚀 Future Enhancements

- [ ] Real-time streaming with Kafka/Apache Flink
- [ ] Machine learning models for traffic prediction
- [ ] Mobile app integration
- [ ] Multi-city support
- [ ] Weather data integration
- [ ] Incident detection and alerts

## 📚 Technologies Used

- **PySpark** - Distributed data processing
- **Pandas/NumPy** - Data manipulation
- **Gradio** - Web UI framework
- **Google Gemini AI** - LLM for decision justification
- **Grafana** - Data visualization
- **Prometheus** - Metrics collection
- **Python-dotenv** - Environment management

## 📝 License

MIT License - feel free to use this project for learning or development.

## 🙏 Acknowledgments

- Traffic simulation concepts based on real-world traffic management systems
- Congestion index calculations inspired by TomTom Traffic Index
- Built as a comprehensive case study for data engineering and AI integration

## 📧 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the code comments
3. Test each component individually

---

## macOS launchd integration & orchestrator

This repository now includes a consolidated orchestrator script at `scripts/traffic_control.sh` which can start/stop/status/smoke the whole stack (docker-compose, ETL, metrics exporter, Gradio UI).

Key usage examples:

```bash
# Start everything (docker-compose + ETL + exporter + Gradio)
scripts/traffic_control.sh start

# Start but skip Docker (useful on machines without Docker or for isolated testing)
scripts/traffic_control.sh start --no-docker
# or
NO_DOCKER=true scripts/traffic_control.sh start

# Stop everything
scripts/traffic_control.sh stop

# Check status
scripts/traffic_control.sh status

# Run a smoke workflow (generate data, run ETL, start exporter and check /metrics)
scripts/traffic_control.sh smoke
```

A sample launchd plist is included at `launchd/com.trafficcontrol.stack.plist`. To install it for your user:

```bash
cp launchd/com.trafficcontrol.stack.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.trafficcontrol.stack.plist

# To unload/stop:
launchctl unload ~/Library/LaunchAgents/com.trafficcontrol.stack.plist
```

Notes:
- If Docker isn't available at boot, either edit the plist to include `--no-docker` in ProgramArguments or set `NO_DOCKER=true` in the plist's `EnvironmentVariables`.
- Logs from launchd runs are written to `logs/launchd.out` and `logs/launchd.err` in the repo root.


**Built with ❤️ for Smart City Solutions**
"""

print("README.md")
print("=" * 60)
print(readme_content)
