#!/usr/bin/env bash
#
# 🚦 Smart Traffic Control System - Launch Script
# Complete orchestration for all services
#

set -euo pipefail

# Configuration
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/venv"
LOG_DIR="$ROOT_DIR/logs"
PIDS_DIR="$ROOT_DIR/.pids"

# Service ports
METRICS_PORT=8000
GRADIO_PORT=7860
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Create directories
mkdir -p "$LOG_DIR" "$PIDS_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo "================================================================="
    echo "🚦 SMART TRAFFIC CONTROL SYSTEM"
    echo "================================================================="
    echo ""
}

print_separator() {
    echo "================================================================="
}

# Activate virtual environment
activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        log_info "Activating virtual environment..."
        # shellcheck disable=SC1090
        source "$VENV_DIR/bin/activate"
        log_success "Virtual environment activated"
    else
        log_warning "Virtual environment not found at $VENV_DIR"
        log_info "Using system Python"
    fi
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python not found. Please install Python 3.9+"
        exit 1
    fi
    log_success "Python found: $PYTHON_CMD"
}

# Check if process is running
is_running() {
    local pidfile="$1"
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Generate synthetic traffic data
generate_data() {
    log_info "Generating synthetic traffic data..."
    if $PYTHON_CMD "$ROOT_DIR/src/data_generator.py"; then
        log_success "Data generation complete"
        local count=$(wc -l < "$ROOT_DIR/data/raw/traffic_sensor_data.csv" | tr -d ' ')
        log_info "Generated $count sensor readings"
    else
        log_error "Data generation failed"
        return 1
    fi
}

# Run ETL pipeline
run_etl() {
    log_info "Running PySpark ETL pipeline..."
    if $PYTHON_CMD "$ROOT_DIR/src/etl_pipeline.py" > "$LOG_DIR/etl.log" 2>&1; then
        log_success "ETL pipeline completed successfully"
        log_info "Processed data saved to data/processed/"
    else
        log_error "ETL pipeline failed. Check $LOG_DIR/etl.log"
        return 1
    fi
}

# Start metrics exporter
start_metrics_exporter() {
    local pidfile="$PIDS_DIR/metrics_exporter.pid"
    
    if is_running "$pidfile"; then
        log_warning "Metrics exporter already running (PID: $(cat $pidfile))"
        return 0
    fi
    
    log_info "Starting Prometheus metrics exporter..."
    nohup $PYTHON_CMD "$ROOT_DIR/src/metrics_exporter.py" > "$LOG_DIR/metrics_exporter.log" 2>&1 &
    echo $! > "$pidfile"
    
    # Wait for service to start
    sleep 3
    
    if curl -s "http://localhost:$METRICS_PORT/metrics" > /dev/null 2>&1; then
        log_success "Metrics exporter running on port $METRICS_PORT (PID: $(cat $pidfile))"
    else
        log_error "Metrics exporter failed to start. Check $LOG_DIR/metrics_exporter.log"
        return 1
    fi
}

# Start Gradio UI
start_gradio() {
    local pidfile="$PIDS_DIR/gradio.pid"
    
    if is_running "$pidfile"; then
        log_warning "Gradio UI already running (PID: $(cat $pidfile))"
        return 0
    fi
    
    log_info "Starting Gradio UI..."
    nohup $PYTHON_CMD "$ROOT_DIR/src/gradio_ui.py" > "$LOG_DIR/gradio.log" 2>&1 &
    echo $! > "$pidfile"
    
    # Wait for service to start
    sleep 5
    
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$GRADIO_PORT" | grep -q "200"; then
        log_success "Gradio UI running on port $GRADIO_PORT (PID: $(cat $pidfile))"
        log_info "Access UI at: http://localhost:$GRADIO_PORT"
    else
        log_warning "Gradio UI may still be starting. Check $LOG_DIR/gradio.log"
    fi
}

# Start Docker services
start_docker() {
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        log_warning "Docker not found. Skipping Grafana/Prometheus."
        return 0
    fi
    
    log_info "Starting Docker services (Prometheus + Grafana)..."
    
    if docker-compose -f "$ROOT_DIR/docker-compose.yml" up -d prometheus grafana 2>/dev/null; then
        log_success "Docker services started"
        log_info "Prometheus: http://localhost:$PROMETHEUS_PORT"
        log_info "Grafana: http://localhost:$GRAFANA_PORT (admin/admin)"
    else
        log_warning "Docker services failed to start. Continuing without Grafana."
    fi
}

# Stop all services
stop_services() {
    log_info "Stopping all services..."
    
    # Stop Python processes
    for service in metrics_exporter gradio; do
        local pidfile="$PIDS_DIR/${service}.pid"
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping $service (PID: $pid)"
                kill "$pid" 2>/dev/null || true
                rm -f "$pidfile"
            fi
        fi
    done
    
    # Extra cleanup
    pkill -f "src/metrics_exporter.py" 2>/dev/null || true
    pkill -f "src/gradio_ui.py" 2>/dev/null || true
    
    # Stop Docker services
    if command -v docker-compose &> /dev/null; then
        log_info "Stopping Docker services..."
        docker-compose -f "$ROOT_DIR/docker-compose.yml" down 2>/dev/null || true
    fi
    
    log_success "All services stopped"
}

# Check status of all services
check_status() {
    print_header
    echo "📊 SERVICE STATUS"
    print_separator
    
    # Data files
    echo ""
    echo "1️⃣  Data Generation:"
    if [ -f "$ROOT_DIR/data/raw/traffic_sensor_data.csv" ]; then
        local count=$(wc -l < "$ROOT_DIR/data/raw/traffic_sensor_data.csv" | tr -d ' ')
        log_success "Traffic sensor data exists ($count lines)"
    else
        log_error "Traffic sensor data missing"
    fi
    
    # ETL output
    echo ""
    echo "2️⃣  ETL Pipeline Output:"
    if [ -d "$ROOT_DIR/data/processed/enriched_data" ]; then
        local parquet_count=$(ls -1 "$ROOT_DIR/data/processed/enriched_data"/*.parquet 2>/dev/null | wc -l | tr -d ' ')
        log_success "Enriched data (Parquet): $parquet_count files"
    else
        log_error "Enriched data missing"
    fi
    
    if [ -d "$ROOT_DIR/data/processed/enriched_data_csv" ]; then
        local csv_count=$(ls -1 "$ROOT_DIR/data/processed/enriched_data_csv"/*.csv 2>/dev/null | wc -l | tr -d ' ')
        log_success "Enriched data (CSV): $csv_count files"
    else
        log_error "Enriched CSV missing"
    fi
    
    # Metrics exporter
    echo ""
    echo "3️⃣  Metrics Exporter:"
    if is_running "$PIDS_DIR/metrics_exporter.pid"; then
        local pid=$(cat "$PIDS_DIR/metrics_exporter.pid")
        log_success "Running on port $METRICS_PORT (PID: $pid)"
        if curl -s "http://localhost:$METRICS_PORT/metrics" > /dev/null 2>&1; then
            echo "   📊 Sample metrics:"
            curl -s "http://localhost:$METRICS_PORT/metrics" | grep "traffic_congestion_index{" | head -3 | sed 's/^/      /'
        fi
    else
        log_error "Not running"
    fi
    
    # Gradio UI
    echo ""
    echo "4️⃣  Gradio UI:"
    if is_running "$PIDS_DIR/gradio.pid"; then
        local pid=$(cat "$PIDS_DIR/gradio.pid")
        log_success "Running on port $GRADIO_PORT (PID: $pid)"
        log_info "Access at: http://localhost:$GRADIO_PORT"
    else
        log_error "Not running"
    fi
    
    # Docker services
    echo ""
    echo "5️⃣  Docker Services:"
    if command -v docker-compose &> /dev/null; then
        if docker-compose -f "$ROOT_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "Up"; then
            log_success "Docker services running"
            log_info "Prometheus: http://localhost:$PROMETHEUS_PORT"
            log_info "Grafana: http://localhost:$GRAFANA_PORT"
        else
            log_warning "Docker services not running"
        fi
    else
        log_warning "Docker not available"
    fi
    
    print_separator
}

# Full system start
start_all() {
    print_header
    log_info "Starting Smart Traffic Control System..."
    print_separator
    
    # Activate venv and check Python
    activate_venv
    check_python
    
    # Generate data if not exists
    if [ ! -f "$ROOT_DIR/data/raw/traffic_sensor_data.csv" ]; then
        generate_data
    else
        log_info "Data already exists. Skipping generation."
    fi
    
    # Run ETL if processed data doesn't exist
    if [ ! -d "$ROOT_DIR/data/processed/enriched_data" ]; then
        run_etl
    else
        log_info "Processed data exists. Skipping ETL."
    fi
    
    # Start services
    start_metrics_exporter
    start_gradio
    start_docker
    
    print_separator
    log_success "All services started!"
    echo ""
    echo "📍 Access Points:"
    echo "   • Gradio UI:    http://localhost:$GRADIO_PORT"
    echo "   • Metrics:      http://localhost:$METRICS_PORT/metrics"
    echo "   • Prometheus:   http://localhost:$PROMETHEUS_PORT"
    echo "   • Grafana:      http://localhost:$GRAFANA_PORT (admin/admin)"
    echo ""
    echo "📝 Logs are in: $LOG_DIR"
    print_separator
}

# Restart services
restart_all() {
    log_info "Restarting all services..."
    stop_services
    sleep 2
    start_all
}

# Run full workflow (smoke test)
run_workflow() {
    print_header
    log_info "Running complete workflow..."
    print_separator
    
    activate_venv
    check_python
    
    # Step 1: Generate data
    generate_data
    
    # Step 2: Run ETL
    run_etl
    
    # Step 3: Start services
    start_metrics_exporter
    start_gradio
    
    # Step 4: Verify
    sleep 5
    log_info "Verifying services..."
    
    if curl -s "http://localhost:$METRICS_PORT/metrics" | grep -q "traffic_vehicle_count"; then
        log_success "Metrics endpoint verified"
    else
        log_error "Metrics endpoint check failed"
    fi
    
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$GRADIO_PORT" | grep -q "200"; then
        log_success "Gradio UI verified"
    else
        log_warning "Gradio UI may still be starting"
    fi
    
    print_separator
    log_success "Workflow complete!"
}

# Show usage
usage() {
    cat <<EOF
🚦 Smart Traffic Control System - Launch Script

Usage: $0 [COMMAND]

Commands:
  start       Start all services (metrics exporter, Gradio UI, Docker)
  stop        Stop all services
  restart     Restart all services
  status      Check status of all services
  workflow    Run complete workflow (generate data → ETL → start services)
  generate    Generate synthetic traffic data only
  etl         Run ETL pipeline only
  help        Show this help message

Examples:
  $0 start              # Start everything
  $0 status             # Check what's running
  $0 workflow           # Run full workflow from scratch
  $0 stop               # Stop all services

Logs: $LOG_DIR
PIDs:  $PIDS_DIR

EOF
}

# Main command handler
main() {
    case "${1:-help}" in
        start)
            start_all
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_all
            ;;
        status)
            check_status
            ;;
        workflow)
            run_workflow
            ;;
        generate)
            activate_venv
            check_python
            generate_data
            ;;
        etl)
            activate_venv
            check_python
            run_etl
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "Unknown command: $1"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
