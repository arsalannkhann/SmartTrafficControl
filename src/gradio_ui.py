
"""
gradio_ui.py
Gradio UI with Gemini API integration for traffic light decisions
"""

import gradio as gr
import pandas as pd
import os
from dotenv import load_dotenv
import glob
from datetime import datetime
import time
import random
import threading

# Note: Google Gemini integration requires the appropriate SDK and API key.
try:
    import google.generativeai as genai  # optional import; may not be installed in dev env
except Exception:
    genai = None

# Optional Cohere import (preferred if COHERE_API_KEY is provided)
try:
    import cohere
except Exception:
    cohere = None

# Load environment variables
load_dotenv()


class TrafficControlUI:
    """Gradio interface for Smart Traffic Control System"""

    def __init__(self):
        self.streaming_active = False
        self.streaming_thread = None
        self.current_simulated_data = {}
        api_key = os.getenv("GEMINI_API_KEY")
        cohere_key = os.getenv("COHERE_API_KEY")
        if genai and api_key:
            genai.configure(api_key=api_key)
            try:
                # Try multiple model names for compatibility
                try:
                    self.model = genai.GenerativeModel("gemini-pro")
                except:
                    try:
                        self.model = genai.GenerativeModel("models/gemini-pro")
                    except:
                        self.model = None
            except Exception as e:
                print(f"Warning: Could not initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None

        # Cohere client (optional). If COHERE_API_KEY is provided we prefer Cohere.
        if cohere and cohere_key:
            try:
                self.cohere_client = cohere.Client(api_key=cohere_key)
            except Exception:
                self.cohere_client = None
        else:
            self.cohere_client = None

        self.data_path = "data/processed"

    def _read_latest_csv(self, pattern):
        """Read the latest CSV file"""
        files = glob.glob(os.path.join(self.data_path, pattern))
        if not files:
            return None
        latest_file = max(files, key=os.path.getctime)
        return pd.read_csv(latest_file)

    def get_intersection_data(self, intersection_id):
        """Get data for a specific intersection"""
        try:
            enriched_df = self._read_latest_csv("enriched_data_csv/*.csv")
            hourly_df = self._read_latest_csv("hourly_metrics_csv/*.csv")

            if enriched_df is None or hourly_df is None:
                return None, None

            int_data = enriched_df[enriched_df["intersection_id"] == intersection_id]
            hourly_data = hourly_df[hourly_df["intersection_id"] == intersection_id]

            return int_data, hourly_data

        except Exception as e:
            print(f"Error reading data: {e}")
            return None, None

    def _generate_rule_based_justification(self, tci, vehicle_count, avg_speed, location):
        """Generate intelligent rule-based traffic justification"""
        if tci < 20:
            return f"Traffic at {location} is flowing smoothly with a low congestion index of {tci:.1f}. " \
                   f"The current vehicle count of {vehicle_count:.0f} vehicles per 5 minutes and average speed of {avg_speed:.1f} mph " \
                   f"indicate normal conditions. Standard 45-second green light cycle is sufficient to maintain optimal flow."
        elif tci < 40:
            return f"Traffic at {location} shows light congestion with a TCI of {tci:.1f}. " \
                   f"With {vehicle_count:.0f} vehicles in the last 5 minutes traveling at {avg_speed:.1f} mph, " \
                   f"a moderate 55-second green cycle is recommended to prevent queue buildup while maintaining efficiency."
        elif tci < 60:
            return f"Moderate congestion detected at {location} (TCI: {tci:.1f}). " \
                   f"The intersection is handling {vehicle_count:.0f} vehicles per 5 minutes at {avg_speed:.1f} mph. " \
                   f"An extended 65-second green light cycle will help clear the increased traffic volume and reduce wait times."
        elif tci < 80:
            return f"High congestion alert at {location} with TCI of {tci:.1f}. " \
                   f"Traffic volume of {vehicle_count:.0f} vehicles and reduced speed of {avg_speed:.1f} mph indicate significant delays. " \
                   f"Priority 75-second green cycle is necessary to manage the heavy traffic load and prevent gridlock."
        else:
            return f"CRITICAL congestion at {location}! TCI has reached {tci:.1f}. " \
                   f"With {vehicle_count:.0f} vehicles per 5 minutes and severely reduced speeds of {avg_speed:.1f} mph, " \
                   f"maximum 90-second green light cycle is required to clear the backlog and restore normal flow. " \
                   f"Consider alternative route recommendations for incoming traffic."

    def generate_traffic_decision(self, intersection_id):
        """Generate AI-driven traffic light decision using Gemini (if available)"""
        int_data, hourly_data = self.get_intersection_data(intersection_id)

        if int_data is None or int_data.empty:
            return {
                "status": "❌ Error",
                "message": "No data available for this intersection. Please run the ETL pipeline first.",
                "ai_justification": "",
            }

        latest = int_data.iloc[-1]

        if hourly_data is not None and not hourly_data.empty:
            avg_congestion = hourly_data["avg_congestion_index"].mean()
            peak_hour = hourly_data.loc[hourly_data["avg_congestion_index"].idxmax(), "hour"]
        else:
            avg_congestion = latest.get("traffic_congestion_index", 0)
            peak_hour = latest.get("hour", 0)

        context = f"""
You are an AI traffic management system analyzing real-time traffic data.

Intersection: {latest.get('location')}
Current Hour: {int(latest.get('hour', 0))}:00
Vehicle Count (last 5m): {latest.get('vehicle_count', 0)}
Average Speed: {latest.get('average_speed', 0):.1f} mph
Traffic Congestion Index: {latest.get('traffic_congestion_index', 0):.1f}
"""

        # Generate AI justification with fallback
        tci = latest.get("traffic_congestion_index", 0)
        vehicle_count = latest.get("vehicle_count", 0)
        avg_speed = latest.get("average_speed", 0)
        location = latest.get("location", "Unknown")
        
        # Default rule-based justification
        ai_justification = self._generate_rule_based_justification(tci, vehicle_count, avg_speed, location)

        # Try AI models if available
        if self.cohere_client is not None:
            try:
                resp = self.cohere_client.generate(
                    model="command-xlarge-nightly",
                    prompt=context,
                    max_tokens=160,
                    temperature=0.5,
                )
                ai_justification = "\n".join([g.text for g in resp.generations])
            except Exception as e:
                pass  # Keep rule-based justification
        elif self.model is not None:
            try:
                response = self.model.generate_content(context)
                ai_justification = getattr(response, "text", str(response))
            except Exception as e:
                pass  # Keep rule-based justification

        # Dynamic signal timing based on TCI
        tci = latest.get("traffic_congestion_index", 0)
        
        if tci < 20:
            signal_duration = "45 seconds green, standard cycle"
            status = "🟢 Normal Flow"
        elif tci < 40:
            signal_duration = "55 seconds green, moderate cycle"
            status = "🟢 Light Congestion"
        elif tci < 60:
            signal_duration = "65 seconds green, extended cycle"
            status = "🟡 Moderate Congestion"
        elif tci < 80:
            signal_duration = "75 seconds green, priority cycle"
            status = "🟠 High Congestion"
        else:
            signal_duration = "90 seconds green, maximum cycle"
            status = "🔴 Critical Congestion"

        return {
            "status": status,
            "intersection": latest.get("location"),
            "timestamp": f"{int(latest.get('hour', 0))}:00",
            "vehicle_count": int(latest.get("vehicle_count", 0)),
            "avg_speed": f"{latest.get('average_speed', 0):.1f} mph",
            "congestion_index": f"{latest.get('traffic_congestion_index', 0):.1f}/100",
            "congestion_level": latest.get("congestion_level", "Unknown"),
            "signal_timing": signal_duration,
            "ai_justification": ai_justification,
        }

    def format_decision_output(self, decision):
        if "message" in decision:
            return decision["message"]

        output = f"""
## 🚦 Traffic Control Decision
**Status:** {decision['status']}
**Intersection:** {decision['intersection']}
**Time:** {decision['timestamp']}

### 📊 Current Metrics
- **Vehicle Count:** {decision['vehicle_count']} vehicles (last 5 min)
- **Average Speed:** {decision['avg_speed']}
- **Congestion Index:** {decision['congestion_index']}
- **Congestion Level:** {decision['congestion_level']}

### ⏱️ Signal Timing Decision
**{decision['signal_timing']}**

### 🤖 AI Justification
{decision['ai_justification']}
"""
        return output

    def generate_simulated_traffic_data(self, intersection_id, base_hour=None):
        """Generate realistic simulated traffic data with varying congestion"""
        if base_hour is None:
            base_hour = datetime.now().hour
        
        # Simulate rush hour patterns
        is_morning_rush = 7 <= base_hour <= 9
        is_evening_rush = 17 <= base_hour <= 19
        is_night = 22 <= base_hour or base_hour <= 5
        
        # Base values
        if is_morning_rush or is_evening_rush:
            base_tci = random.uniform(50, 90)
            base_vehicles = random.randint(80, 150)
            base_speed = random.uniform(20, 35)
        elif is_night:
            base_tci = random.uniform(2, 15)
            base_vehicles = random.randint(5, 25)
            base_speed = random.uniform(45, 55)
        else:
            base_tci = random.uniform(15, 45)
            base_vehicles = random.randint(30, 70)
            base_speed = random.uniform(30, 50)
        
        # Add random variation
        tci = max(0, min(100, base_tci + random.uniform(-10, 10)))
        vehicle_count = max(0, int(base_vehicles + random.randint(-15, 15)))
        avg_speed = max(10, min(55, base_speed + random.uniform(-5, 5)))
        
        # Determine congestion level
        if tci < 20:
            congestion_level = "Low"
        elif tci < 40:
            congestion_level = "Moderate"
        elif tci < 60:
            congestion_level = "High"
        elif tci < 80:
            congestion_level = "Severe"
        else:
            congestion_level = "Critical"
        
        return {
            "traffic_congestion_index": tci,
            "vehicle_count": vehicle_count,
            "average_speed": avg_speed,
            "congestion_level": congestion_level,
            "hour": base_hour,
            "location": intersection_id.split(" - ")[1] if " - " in intersection_id else "Unknown"
        }

    def generate_streaming_decision(self, intersection_choice, enable_streaming):
        """Generate traffic decision with optional real-time streaming"""
        if not intersection_choice or "No data" in intersection_choice or "Error" in intersection_choice:
            return "⚠️ Please run the ETL pipeline first to generate data.", "🔴 Streaming: OFF"
        
        intersection_id = intersection_choice.split(" - ")[0]
        
        # Use simulated data if streaming is enabled
        if enable_streaming:
            simulated_data = self.generate_simulated_traffic_data(intersection_choice)
            
            # Create a mock latest record
            latest = simulated_data
            tci = latest["traffic_congestion_index"]
            vehicle_count = latest["vehicle_count"]
            avg_speed = latest["average_speed"]
            location = latest["location"]
            
            # Generate AI justification
            ai_justification = self._generate_rule_based_justification(tci, vehicle_count, avg_speed, location)
            
            # Determine signal timing
            if tci < 20:
                signal_duration = "45 seconds green, standard cycle"
                status = "🟢 Normal Flow"
            elif tci < 40:
                signal_duration = "55 seconds green, moderate cycle"
                status = "🟢 Light Congestion"
            elif tci < 60:
                signal_duration = "65 seconds green, extended cycle"
                status = "🟡 Moderate Congestion"
            elif tci < 80:
                signal_duration = "75 seconds green, priority cycle"
                status = "🟠 High Congestion"
            else:
                signal_duration = "90 seconds green, maximum cycle"
                status = "🔴 Critical Congestion"
            
            decision = {
                "status": status,
                "intersection": location,
                "timestamp": f"{int(latest['hour'])}:00 (SIMULATED)",
                "vehicle_count": int(vehicle_count),
                "avg_speed": f"{avg_speed:.1f} mph",
                "congestion_index": f"{tci:.1f}/100",
                "congestion_level": latest["congestion_level"],
                "signal_timing": signal_duration,
                "ai_justification": ai_justification,
            }
            
            streaming_status = f"🟢 Streaming: ON | TCI: {tci:.1f} | Updated: {datetime.now().strftime('%H:%M:%S')}"
        else:
            # Use real data
            decision = self.generate_traffic_decision(intersection_id)
            streaming_status = "🔴 Streaming: OFF (Using historical data)"
        
        return self.format_decision_output(decision), streaming_status

    def create_interface(self):
        with gr.Blocks(title="Smart Traffic Control System", theme=gr.themes.Soft()) as demo:
            gr.Markdown("""
            # 🚦 Smart Traffic Control System
            ### AI-Powered Traffic Light Optimization
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🎯 Select Intersection")

                    try:
                        stats_df = self._read_latest_csv("intersection_stats_csv/*.csv")
                        if stats_df is not None:
                            intersections = stats_df["intersection_id"].tolist()
                            locations = stats_df["location"].tolist()
                            choices = [f"{iid} - {loc}" for iid, loc in zip(intersections, locations)]
                        else:
                            choices = ["No data available - Run ETL pipeline first"]
                    except Exception:
                        choices = ["Error loading intersections"]

                    intersection_dropdown = gr.Dropdown(choices=choices, label="Choose Intersection")
                    
                    gr.Markdown("### 🔄 Real-Time Streaming")
                    streaming_toggle = gr.Checkbox(
                        label="Enable Real-Time Streaming", 
                        value=False,
                        info="Simulate live traffic with varying congestion levels"
                    )
                    
                    analyze_btn = gr.Button("🔍 Analyze & Generate Decision", variant="primary", size="lg")
                    
                    gr.Markdown("---")
                    streaming_status = gr.Markdown("🔴 Streaming: OFF")

                with gr.Column(scale=2):
                    output_display = gr.Markdown("### Select an intersection and click Analyze to begin")

            # Event handler for analysis with streaming support
            analyze_btn.click(
                fn=self.generate_streaming_decision,
                inputs=[intersection_dropdown, streaming_toggle],
                outputs=[output_display, streaming_status]
            )
            
            # Auto-update when streaming toggle changes
            streaming_toggle.change(
                fn=self.generate_streaming_decision,
                inputs=[intersection_dropdown, streaming_toggle],
                outputs=[output_display, streaming_status]
            )

        return demo

    def launch(self, share=False):
        demo = self.create_interface()
        demo.launch(share=share, server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    app = TrafficControlUI()
    app.launch(share=False)
