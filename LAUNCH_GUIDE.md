# 🚀 Launch Guide - Smart Traffic Control System

## Quick Start

### One-Command Launch
```bash
./launch.sh start
```

This will:
1. ✅ Activate virtual environment
2. ✅ Check if data exists (generate if needed)
3. ✅ Check if ETL ran (process if needed)
4. ✅ Start metrics exporter (port 8000)
5. ✅ Start Gradio UI (port 7860)
6. ✅ Start Docker services (Grafana + Prometheus)

---

## 📋 Available Commands

### `./launch.sh start`
Start all services (smart - skips data generation and ETL if already done)

### `./launch.sh stop`
Stop all running services gracefully

### `./launch.sh restart`
Restart all services

### `./launch.sh status`
Check status of all components

### `./launch.sh workflow`
Run complete workflow from scratch:
- Generate data
- Run ETL pipeline
- Start all services
- Verify everything works

### `./launch.sh generate`
Generate synthetic traffic data only

### `./launch.sh etl`
Run ETL pipeline only

### `./launch.sh help`
Show help message

---

## 🌐 Access Points

Once started, access your services at:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Gradio UI** | http://localhost:7860 | None |
| **Metrics** | http://localhost:8000/metrics | None |
| **Prometheus** | http://localhost:9090 | None |
| **Grafana** | http://localhost:3000 | admin/admin |

---

## 📊 What's Running?

### Metrics Exporter (Port 8000)
- Exports Prometheus-format metrics
- Updates every 30 seconds
- Provides 4 metric types:
  - `traffic_vehicle_count`
  - `traffic_average_speed`
  - `traffic_congestion_index`
  - `traffic_congestion_level`

**Test it:**
```bash
curl http://localhost:8000/metrics
```

### Gradio UI (Port 7860)
- Interactive web interface
- Select intersections
- View real-time metrics
- Get AI-powered recommendations

**Test it:**
```bash
curl -I http://localhost:7860
# Should return: HTTP/1.1 200 OK
```

### Prometheus (Port 9090)
- Scrapes metrics from exporter
- Stores time-series data
- Provides query interface

### Grafana (Port 3000)
- Visualizes Prometheus data
- Pre-configured dashboards
- Real-time monitoring

---

## 🔍 Verification

### Quick Status Check
```bash
./launch.sh status
```

### Manual Verification

**1. Check Metrics Exporter:**
```bash
curl -s http://localhost:8000/metrics | grep "traffic_vehicle_count" | head -5
```

**2. Check Gradio UI:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:7860
# Should output: 200
```

**3. Check Prometheus:**
```bash
curl -s http://localhost:9090/-/healthy
# Should output: Prometheus is Healthy.
```

**4. Check Grafana:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Should output: 200
```

---

## 📁 File Locations

### Logs
All service logs are in: `logs/`
- `logs/etl.log` - ETL pipeline output
- `logs/metrics_exporter.log` - Metrics exporter logs
- `logs/gradio.log` - Gradio UI logs

### Process IDs
PID files are in: `.pids/`
- `.pids/metrics_exporter.pid`
- `.pids/gradio.pid`

### Data
- `data/raw/` - Raw sensor data
- `data/processed/` - Processed Parquet and CSV files

---

## 🔧 Troubleshooting

### Services Won't Start

**Check Python:**
```bash
python3 --version
# Should be 3.9 or higher
```

**Check Virtual Environment:**
```bash
source venv/bin/activate
pip list | grep -E "(pyspark|gradio|prometheus)"
```

**Reinstall Dependencies:**
```bash
./venv/bin/pip install -r requirements.txt
```

### Port Already in Use

**Check what's using the port:**
```bash
lsof -i :8000  # Metrics exporter
lsof -i :7860  # Gradio UI
lsof -i :9090  # Prometheus
lsof -i :3000  # Grafana
```

**Kill process:**
```bash
kill -9 <PID>
```

### Metrics Not Updating

**Restart metrics exporter:**
```bash
./launch.sh stop
./launch.sh start
```

**Check logs:**
```bash
tail -f logs/metrics_exporter.log
```

### Gradio UI Not Loading

**Check if it's running:**
```bash
ps aux | grep gradio_ui
```

**Check logs:**
```bash
tail -f logs/gradio.log
```

**Restart:**
```bash
pkill -f gradio_ui.py
./launch.sh start
```

### Docker Services Failing

**Check Docker status:**
```bash
docker --version
docker-compose --version
```

**View Docker logs:**
```bash
docker-compose logs prometheus
docker-compose logs grafana
```

**Restart Docker:**
```bash
docker-compose down
docker-compose up -d
```

---

## 🎯 Common Workflows

### First Time Setup
```bash
# 1. Install dependencies
./venv/bin/pip install -r requirements.txt

# 2. Run complete workflow
./launch.sh workflow

# 3. Access Gradio UI
open http://localhost:7860
```

### Daily Use
```bash
# Start everything
./launch.sh start

# Check status
./launch.sh status

# Stop when done
./launch.sh stop
```

### Regenerate Data
```bash
# Stop services
./launch.sh stop

# Remove old data
rm -rf data/raw/* data/processed/*

# Run workflow
./launch.sh workflow
```

### Update Code
```bash
# Stop services
./launch.sh stop

# Pull latest code
git pull

# Restart
./launch.sh start
```

---

## 📈 Monitoring

### Watch Metrics in Real-Time
```bash
watch -n 2 'curl -s http://localhost:8000/metrics | grep "traffic_congestion_index"'
```

### Monitor Logs
```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/gradio.log
```

### Check Resource Usage
```bash
ps aux | grep -E "(metrics_exporter|gradio_ui)" | grep -v grep
```

---

## 🚀 Production Deployment

### Environment Variables
Create `.env` file:
```bash
GEMINI_API_KEY=your_key_here
COHERE_API_KEY=your_key_here  # Optional
```

### Systemd Service (Linux)
```bash
# Copy service file
sudo cp systemd/traffic-control.service /etc/systemd/system/

# Enable and start
sudo systemctl enable traffic-control
sudo systemctl start traffic-control

# Check status
sudo systemctl status traffic-control
```

### Launchd (macOS)
```bash
# Copy plist
cp launchd/com.trafficcontrol.stack.plist ~/Library/LaunchAgents/

# Load
launchctl load ~/Library/LaunchAgents/com.trafficcontrol.stack.plist

# Check status
launchctl list | grep trafficcontrol
```

---

## 🎨 Customization

### Change Ports

Edit `launch.sh`:
```bash
METRICS_PORT=8000    # Change to your port
GRADIO_PORT=7860     # Change to your port
```

### Adjust Update Interval

Edit `src/metrics_exporter.py`:
```python
exporter.start(update_interval=30)  # Change to your interval
```

### Add More Intersections

Edit `src/data_generator.py`:
```python
generator = TrafficDataGenerator(num_intersections=50, hours=48)
```

---

## 📊 Expected Output

### Successful Start
```
=================================================================
🚦 SMART TRAFFIC CONTROL SYSTEM
=================================================================

ℹ️  Starting Smart Traffic Control System...
=================================================================
ℹ️  Activating virtual environment...
✅ Virtual environment activated
✅ Python found: python3
ℹ️  Data already exists. Skipping generation.
ℹ️  Processed data exists. Skipping ETL.
ℹ️  Starting Prometheus metrics exporter...
✅ Metrics exporter running on port 8000 (PID: 12345)
ℹ️  Starting Gradio UI...
✅ Gradio UI running on port 7860 (PID: 12346)
ℹ️  Access UI at: http://localhost:7860
ℹ️  Starting Docker services (Prometheus + Grafana)...
✅ Docker services started
ℹ️  Prometheus: http://localhost:9090
ℹ️  Grafana: http://localhost:3000 (admin/admin)
=================================================================
✅ All services started!

📍 Access Points:
   • Gradio UI:    http://localhost:7860
   • Metrics:      http://localhost:8000/metrics
   • Prometheus:   http://localhost:9090
   • Grafana:      http://localhost:3000 (admin/admin)

📝 Logs are in: logs
=================================================================
```

### Status Check
```
=================================================================
🚦 SMART TRAFFIC CONTROL SYSTEM
=================================================================

📊 SERVICE STATUS
=================================================================

1️⃣  Data Generation:
✅ Traffic sensor data exists (5761 lines)

2️⃣  ETL Pipeline Output:
✅ Enriched data (Parquet): 1 files
✅ Enriched data (CSV): 1 files

3️⃣  Metrics Exporter:
✅ Running on port 8000 (PID: 12345)
   📊 Sample metrics:
      traffic_congestion_index{intersection_id="INT_001",...} 25.64
      traffic_congestion_index{intersection_id="INT_002",...} 24.89

4️⃣  Gradio UI:
✅ Running on port 7860 (PID: 12346)
ℹ️  Access at: http://localhost:7860

5️⃣  Docker Services:
✅ Docker services running
ℹ️  Prometheus: http://localhost:9090
ℹ️  Grafana: http://localhost:3000
=================================================================
```

---

## ✅ Verification Checklist

- [ ] Virtual environment activated
- [ ] Python 3.9+ installed
- [ ] Dependencies installed (`pip list`)
- [ ] Data generated (5,760+ records)
- [ ] ETL pipeline completed
- [ ] Metrics exporter running (port 8000)
- [ ] Gradio UI accessible (port 7860)
- [ ] Prometheus scraping metrics (port 9090)
- [ ] Grafana dashboards visible (port 3000)
- [ ] All logs clean (no errors)

---

## 🎓 Next Steps

1. **Access Gradio UI:** http://localhost:7860
2. **Select an intersection** from the dropdown
3. **Click "Analyze"** to see AI recommendations
4. **View Grafana dashboards:** http://localhost:3000
5. **Explore Prometheus queries:** http://localhost:9090

---

## 📞 Support

For issues:
1. Check logs in `logs/` directory
2. Run `./launch.sh status` to diagnose
3. Review `SYSTEM_VERIFICATION_REPORT.md`
4. Check `REQUIREMENTS_ANALYSIS.md` for details

---

**Last Updated:** October 31, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready
