#!/usr/bin/env python3
"""scripts/run_smoke.py

Quick smoke-run automation:
- generate synthetic data
- run ETL (PySpark)
- start metrics exporter in background
- check /metrics endpoint
- optionally launch Gradio UI

Run this from the project root with the project's venv activated.
"""
import subprocess
import time
import os
import signal
import sys
import requests

ROOT = os.path.dirname(os.path.dirname(__file__))
METRICS_URL = "http://localhost:8000/metrics"


def run_cmd(cmd, check=True, capture=False):
    print(f"Running: {cmd}")
    if capture:
        return subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    else:
        return subprocess.run(cmd, shell=True, check=check)


def start_exporter():
    # Start metrics exporter as background process and return Popen
    exporter_cmd = "python3 -u src/metrics_exporter.py"
    log = open("/tmp/metrics_exporter.log", "a")
    p = subprocess.Popen(exporter_cmd, shell=True, stdout=log, stderr=log, preexec_fn=os.setsid)
    print(f"Started metrics exporter (pid={p.pid})")
    return p


def check_metrics(timeout=10):
    print(f"Checking metrics endpoint {METRICS_URL} (timeout {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(METRICS_URL, timeout=2)
            if r.status_code == 200 and "traffic_vehicle_count" in r.text:
                print("Metrics endpoint is up and serving metrics")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("Metrics endpoint check failed")
    return False


def main(launch_ui=False):
    cwd = os.getcwd()
    if os.path.basename(cwd) != os.path.basename(ROOT):
        print("Please run this script from the project root (where requirements.txt lives)")
        # continue anyway

    # 1. Generate data
    run_cmd("python3 src/data_generator.py")

    # 2. Run ETL
    run_cmd("python3 src/etl_pipeline.py")

    # 3. Start exporter
    exporter = start_exporter()

    # 4. Check metrics
    ok = check_metrics(timeout=15)

    # 5. Optionally launch Gradio UI
    ui_proc = None
    if launch_ui:
        ui_proc = subprocess.Popen("python3 src/gradio_ui.py", shell=True, preexec_fn=os.setsid)
        print(f"Launched Gradio UI (pid={ui_proc.pid})")

    print("Smoke run complete")
    print("Press Ctrl-C to stop background processes or run the following to clean up:")
    print(f"  kill -TERM {exporter.pid}")
    if ui_proc:
        print(f"  kill -TERM {ui_proc.pid}")


if __name__ == "__main__":
    launch = "--ui" in sys.argv or "-u" in sys.argv
    main(launch_ui=launch)
