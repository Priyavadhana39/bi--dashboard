"""
Module 4: Machine Learning & Predictive Analytics

This module provides three core ML capabilities:
1. Supplier Performance Scoring
2. Price Anomaly Detection  
3. Demand Forecasting

All models use actual procurement data from PostgreSQL.
"""

__version__ = "1.0.0"
__author__ = "Procurement Intelligence System"

from . import data_loader
from . import preprocessing
from . import supplier_scoring
from . import price_anomaly
from . import demand_forecasting
from . import evaluation
from . import pipeline
