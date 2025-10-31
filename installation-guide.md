# 🚦 Smart Traffic Control System - Complete Installation & Usage Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [Running the Project](#running-the-project)
5. [Grafana Dashboard Setup](#grafana-dashboard-setup)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Software Requirements
- **Python**: 3.9 or higher
- **Java**: 11 or higher (required for PySpark)
- **Grafana**: Latest stable version
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Hardware Requirements
- **RAM**: Minimum 8GB (16GB recommended for large datasets)
- **Storage**: 5GB free space
- **CPU**: Multi-core processor recommended for PySpark

### API Requirements
- **Google Gemini API Key**: Free tier available at https://makersuite.google.com/app/apikey

---

## Installation Steps

### Step 1: Install Java (Required for PySpark)

#### Windows
1. Download Java JDK 11 from: https://adoptium.net/
2. Install and add to PATH
3. Verify: `java -version`

#### macOS
```bash
brew install openjdk@11
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install openjdk-11-jdk
java -version
```

### Step 2: Set Up Python Environment

```bash
# Clone or create project directory
mkdir traffic_control_system
cd traffic_control_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Verify Python version
python --version
```

### Step 3: Create Project Structure

```bash
# Create necessary directories
mkdir -p data/raw data/processed src config

# Create empty __init__.py
touch src/__init__.py
```

### Step 4: Install Python Dependencies

Create `requirements.txt` with:
```
pyspark==3.5.0
pandas==2.1.3
numpy==1.24.3
gradio==4.44.0
google-generativeai==0.3.2
python-dotenv==1.0.0
prometheus-client==0.19.0
Faker==20.1.0
pyarrow==14.0.1
```

Install:
```bash
pip install -r requirements.txt
```

### Step 5: Install Grafana

#### Windows
1. Download from: https://grafana.com/grafana/download
2. Run installer
3. Start Grafana service

#### macOS
```bash
brew install grafana
brew services start grafana
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

---

## Configuration

### Step 1: Get Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

### Step 2: Configure Environment Variables

Create `.env` file in project root:
```bash
# Copy from template
cp .env.example .env

# Edit .env file
nano .env  # or use any text editor
```

Add your API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

---

## Running the Project

### Complete Workflow

#### 1. Generate Synthetic Traffic Data
```bash
python src/data_generator.py
```

**Expected Output:**
```
Saved intersection metadata to data/raw/intersection_metadata.csv
Saved sensor data to data/raw/traffic_sensor_data.csv
Generated 5760 sensor readings for 20 intersections
```

**Generated Files:**
- `data/raw/traffic_sensor_data.csv` (~5,760 rows)
- `data/raw/intersection_metadata.csv` (~20 rows)

#### 2. Run PySpark ETL Pipeline
```bash
python src/etl_pipeline.py
```

**Expected Output:**
```
============================================================
Starting Traffic ETL Pipeline
============================================================
Extracting data from data/raw/traffic_sensor_data.csv and data/raw/intersection_metadata.csv
Extracted 5760 sensor records
Extracted 20 intersection records
Starting transformation...
Transformation complete. Total records: 5760
Creating aggregated metrics...
Loading data to data/processed/enriched_data
...
ETL Pipeline Complete!
============================================================
```

**Generated Files:**
- `data/processed/enriched_data/` (Parquet files)
- `data/processed/hourly_metrics/` (Parquet files)
- `data/processed/intersection_stats/` (Parquet files)
- CSV exports for Grafana

#### 3. Start Metrics Exporter (Optional)
```bash
# In a new terminal window
python src/metrics_exporter.py
```

**Access metrics at:** http://localhost:8000/metrics

#### 4. Launch Gradio UI
```bash
python src/gradio_ui.py
```

**Access UI at:** http://localhost:7860

---

## Grafana Dashboard Setup

### Step 1: Access Grafana
1. Open browser: http://localhost:3000
2. Login: **admin** / **admin**
3. Change password when prompted

### Step 2: Add CSV Data Source

1. Click **Configuration** (gear icon) → **Data Sources**
2. Click **Add data source**
3. Search for "CSV"
4. Install CSV plugin if not available
5. Configure:
   - **Name**: Traffic Data
   - **Path**: `<project_path>/data/processed/enriched_data_csv/`

### Step 3: Create Dashboard

#### Panel 1: Traffic Congestion Index Over Time
1. Click **+** → **Dashboard** → **Add new panel**
2. Select **Traffic Data** data source
3. Query:
   - File: `data/processed/hourly_metrics_csv/*.csv`
   - X-axis: `hour`
   - Y-axis: `avg_congestion_index`
4. Visualization: Time series
5. Title: "Traffic Congestion Index - 24 Hour View"

#### Panel 2: Top Congested Intersections
1. Add new panel
2. Query:
   - File: `data/processed/intersection_stats_csv/*.csv`
   - Sort by: `avg_congestion_index` (descending)
   - Limit: 10
3. Visualization: Bar chart
4. Title: "Top 10 Most Congested Intersections"

#### Panel 3: Current Metrics Table
1. Add new panel
2. Query: `intersection_stats_csv/*.csv`
3. Visualization: Table
4. Columns: intersection_id, location, avg_congestion_index, avg_speed
5. Title: "Intersection Statistics"

#### Panel 4: Average Speed by Intersection
1. Add new panel
2. Query: `intersection_stats_csv/*.csv`
3. Visualization: Gauge
4. Field: `avg_speed`
5. Title: "Average Speed (mph)"

### Step 4: Configure Prometheus Data Source (Optional)

If using metrics exporter:

1. Add data source → **Prometheus**
2. URL: `http://localhost:8000`
3. Save & Test

Query examples:
```
traffic_congestion_index{intersection_id="INT_001"}
traffic_average_speed
traffic_vehicle_count
```

---

## Usage Examples

### Example 1: Analyze Specific Intersection

1. Open Gradio UI: http://localhost:7860
2. Select intersection: "INT_001 - Main St & 1st Ave"
3. Click "Analyze & Generate Decision"
4. View:
   - Current traffic status
   - Congestion metrics
   - AI-generated signal timing
   - Detailed justification

### Example 2: Query Data Programmatically

```python
import pandas as pd
import glob

# Read processed data
enriched_path = "data/processed/enriched_data_csv/*.csv"
enriched_files = glob.glob(enriched_path)
df = pd.read_csv(enriched_files[0])

# Find peak congestion hours
peak_hours = df.groupby('hour')['traffic_congestion_index'].mean()
print("Peak Congestion Hours:")
print(peak_hours.sort_values(ascending=False).head())

# Find most congested intersections
top_intersections = df.groupby('location')['traffic_congestion_index'].mean()
print("\nMost Congested Intersections:")
print(top_intersections.sort_values(ascending=False).head())
```

### Example 3: Generate Custom Data

```python
from src.data_generator import TrafficDataGenerator

# Generate data for 50 intersections over 48 hours
generator = TrafficDataGenerator(num_intersections=50, hours=48)
metadata_path, sensor_path = generator.save_to_csv()

print(f"Generated data at: {sensor_path}")
```

### Example 4: Customize ETL Pipeline

```python
from src.etl_pipeline import TrafficETLPipeline

pipeline = TrafficETLPipeline(app_name="CustomTrafficETL")

enriched_df, hourly_metrics, intersection_stats = pipeline.run_pipeline(
    sensor_data_path="data/raw/traffic_sensor_data.csv",
    metadata_path="data/raw/intersection_metadata.csv",
    output_base_path="data/custom_processed"
)

# Show top congested intersections
print("\nTop 10 Congested Intersections:")
intersection_stats.show(10)

pipeline.stop()
```

---

## Troubleshooting

### Issue 1: Java Not Found

**Error:** `Java gateway process exited before sending its port number`

**Solution:**
```bash
# Check Java installation
java -version

# Set JAVA_HOME (Linux/Mac)
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Set JAVA_HOME (Windows)
setx JAVA_HOME "C:\Program Files\Java\jdk-11"
```

### Issue 2: PySpark Import Error

**Error:** `ModuleNotFoundError: No module named 'pyspark'`

**Solution:**
```bash
# Ensure virtual environment is activated
# Reinstall PySpark
pip install --upgrade pyspark
```

### Issue 3: Gemini API Error

**Error:** `google.generativeai.types.generation_types.BlockedPromptException`

**Solution:**
1. Check API key is correct in `.env`
2. Verify API key permissions
3. Check API quota limits

Test API key:
```python
import google.generativeai as genai
genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Hello")
print(response.text)
```

### Issue 4: Grafana Cannot Read CSV Files

**Error:** No data showing in Grafana panels

**Solution:**
1. Verify CSV files exist in `data/processed/*_csv/`
2. Check file permissions
3. Use absolute path in Grafana data source
4. Install CSV plugin: `grafana-cli plugins install marcusolsson-csv-datasource`

### Issue 5: No Data in Gradio UI

**Error:** "No data available for this intersection"

**Solution:**
```bash
# Run ETL pipeline first
python src/etl_pipeline.py

# Verify CSV files exist
ls -la data/processed/enriched_data_csv/
ls -la data/processed/intersection_stats_csv/
```

### Issue 6: Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 7860 (Gradio)
lsof -i :7860  # Mac/Linux
netstat -ano | findstr :7860  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
python src/gradio_ui.py --port 8080
```

### Issue 7: Memory Error with Large Datasets

**Error:** `OutOfMemoryError`

**Solution:**
1. Increase PySpark memory:
```python
# In etl_pipeline.py
spark = SparkSession.builder \
    .appName(app_name) \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()
```

2. Reduce dataset size:
```python
# Generate smaller dataset
generator = TrafficDataGenerator(num_intersections=10, hours=12)
```

---

## Performance Optimization

### For Large Datasets

1. **Partition data properly:**
```python
enriched_df.repartition(4).write.parquet(output_path)
```

2. **Use coalesce instead of repartition:**
```python
df.coalesce(1).write.csv(output_path)
```

3. **Cache frequently used DataFrames:**
```python
enriched_df.cache()
enriched_df.count()  # Materialize cache
```

4. **Adjust Spark configurations:**
```python
spark.conf.set("spark.sql.shuffle.partitions", "200")
spark.conf.set("spark.default.parallelism", "100")
```

---

## Next Steps

After successful setup:

1. **Explore Data:** Analyze patterns in Grafana dashboards
2. **Customize AI Prompts:** Modify Gemini prompts in `gradio_ui.py`
3. **Add Real Data:** Replace synthetic data with real traffic sensors
4. **Deploy to Cloud:** Use AWS/GCP for production deployment
5. **Add Alerts:** Configure Grafana alerts for critical congestion
6. **Build ML Models:** Use processed data for traffic prediction

---

## Support & Resources

- **Documentation:** README.md in project root
- **Grafana Docs:** https://grafana.com/docs/
- **PySpark Docs:** https://spark.apache.org/docs/latest/api/python/
- **Gemini API Docs:** https://ai.google.dev/docs
- **Gradio Docs:** https://gradio.app/docs/

---

**Happy Traffic Optimizing! 🚦**
