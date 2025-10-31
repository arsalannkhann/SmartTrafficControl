
"""
Smart Traffic Control System
A data-driven traffic management system using PySpark, Grafana, and Gemini AI
"""

__version__ = "1.0.0"
__author__ = "Smart City Solutions"

from .data_generator import TrafficDataGenerator
from .etl_pipeline import TrafficETLPipeline

__all__ = ["TrafficDataGenerator", "TrafficETLPipeline"]
