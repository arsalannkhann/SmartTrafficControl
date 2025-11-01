# Time-Series Data Fix for Grafana Dashboard

## Problem
The Grafana dashboard was showing only a single data point because the metrics exporter was reading **static aggregated statistics** (pre-calculated averages) instead of time-series data.

## Root Cause
- Original exporter read from `intersection_stats_csv/` which contains single average values per intersection
- These values never changed, so Prometheus scraped the same values repeatedly
- Grafana displayed flat lines with no historical data

## Solution Applied

### Modified Metrics Exporter
Updated `/src/metrics_exporter.py` to:
1. **Read from `hourly_metrics_csv/`** instead of `intersection_stats_csv/`
2. **Cycle through 24 hours of data** - advances one hour every 30 seconds
3. **Simulate live traffic patterns** by replaying historical hourly data

### Changes Made:
- Added `self.current_hour` tracker to cycle through hours 0-23
- Modified `update_metrics()` to filter hourly data by current hour
- Automatically loops back to hour 0 after hour 23

## How It Works Now

1. **Every 30 seconds**, the exporter:
   - Reads the next hour of traffic data (hour 0, 1, 2, ... 23)
   - Updates metrics with that hour's values
   - Advances to the next hour

2. **Prometheus scrapes** these changing values every 5 seconds

3. **Grafana displays** the time-series with visible trends and patterns

## Verification

Test that values are changing:
```bash
# First reading
curl -s http://localhost:8000/metrics | grep 'traffic_vehicle_count{intersection_id="INT_001"'

# Wait 35 seconds, then check again
# Values should be different
```

## To See the Dashboard Working

1. **Restart all services**:
   ```bash
   ./launch.sh stop
   ./launch.sh start
   ```

2. **Open Grafana**: http://localhost:3000 (admin/admin)

3. **View Traffic Dashboard** - You should now see:
   - Lines that change over time (not flat)
   - Multiple data points across the time range
   - Traffic patterns evolving as hours progress

4. **Time Range**: Set to "Last 15 minutes" or "Last 30 minutes" to see recent data

## Expected Behavior

- **Every 30 seconds**: Metrics update with next hour's data
- **Every 5 seconds**: Prometheus scrapes the new values
- **Dashboard**: Shows smooth time-series graphs with 24 hours of traffic patterns cycling

## Data Source
- **File**: `data/processed/hourly_metrics_csv/part-*.csv`
- **Contains**: 24 hours × 20 intersections = 480 data points
- **Cycles**: Repeats every 12 minutes (24 hours × 30 seconds)
