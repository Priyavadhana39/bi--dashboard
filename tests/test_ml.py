"""
Module 4 ML Tests
Tests for machine learning components.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.data_loader import MLDataLoader
from ml.preprocessing import MLPreprocessor
from ml.supplier_scoring import SupplierScorer
from ml.price_anomaly import PriceAnomalyDetector
from ml.demand_forecasting import DemandForecaster


class TestMLDataLoader:
    """Test ML data loading."""
    
    def test_data_loader_initialization(self):
        """Test that data loader initializes correctly."""
        loader = MLDataLoader()
        assert loader.db is not None
    
    def test_load_purchase_orders(self):
        """Test loading purchase orders."""
        loader = MLDataLoader()
        df = loader.load_purchase_orders()
        
        assert len(df) > 0, "Purchase orders should be loaded"
        assert 'po_id' in df.columns
        assert 'supplier' in df.columns
        assert 'order_date' in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df['order_date'])
    
    def test_load_supplier_aggregates(self):
        """Test loading supplier aggregates."""
        loader = MLDataLoader()
        df = loader.load_supplier_aggregates()
        
        assert len(df) == 5, "Should have 5 suppliers"
        assert 'supplier_id' in df.columns
        assert 'total_orders' in df.columns
        assert 'avg_savings_percentage' in df.columns
    
    def test_load_time_series(self):
        """Test loading time series data."""
        loader = MLDataLoader()
        df = loader.load_overall_time_series()
        
        assert len(df) > 0, "Time series should be loaded"
        assert 'month_date' in df.columns
        assert 'total_quantity' in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df['month_date'])


class TestMLPreprocessor:
    """Test ML preprocessing."""
    
    def test_preprocessor_initialization(self):
        """Test preprocessor initialization."""
        prep = MLPreprocessor()
        assert prep.scalers == {}
    
    def test_prepare_supplier_features(self):
        """Test supplier feature preparation."""
        # Create sample data
        df = pd.DataFrame({
            'supplier_id': [1, 2, 3],
            'supplier': ['A', 'B', 'C'],
            'total_orders': [100, 150, 120],
            'avg_savings_percentage': [8.0, 7.5, 9.0],
            'avg_lead_time_days': [10.0, 12.0, 9.0],
            'avg_defect_rate': [5.0, 8.0, 3.0],
            'compliance_rate': [95.0, 85.0, 98.0],
            'orders_with_delivery': [90, 140, 115],
            'orders_with_defect_data': [80, 130, 110]
        })
        
        prep = MLPreprocessor()
        result = prep.prepare_supplier_features(df)
        
        assert 'savings_score' in result.columns
        assert 'quality_score' in result.columns
        assert 'compliance_score' in result.columns
        assert len(result) == 3
    
    def test_missing_value_handling(self):
        """Test that missing values are NOT treated as zeros."""
        df = pd.DataFrame({
            'value': [1.0, np.nan, 3.0, np.nan, 5.0]
        })
        
        prep = MLPreprocessor()
        
        # Test exclude strategy
        result = prep.handle_missing_values(df, strategy='exclude')
        assert len(result) == 3, "Should exclude 2 rows with NaN"
        assert result['value'].notna().all()


class TestSupplierScorer:
    """Test supplier scoring."""
    
    def test_scorer_initialization(self):
        """Test scorer initialization with weights."""
        scorer = SupplierScorer()
        
        assert scorer.weights is not None
        assert abs(sum(scorer.weights.values()) - 1.0) < 0.01, "Weights should sum to 1.0"
    
    def test_normalize_features(self):
        """Test feature normalization."""
        df = pd.DataFrame({
            'savings_score': [5.0, 10.0, 15.0],
            'quality_score': [80.0, 90.0, 85.0]
        })
        
        scorer = SupplierScorer()
        result = scorer.normalize_features(df)
        
        assert 'savings_score_normalized' in result.columns
        assert 'quality_score_normalized' in result.columns
        assert result['savings_score_normalized'].max() == 100.0
        assert result['savings_score_normalized'].min() == 0.0
    
    def test_score_suppliers(self):
        """Test complete supplier scoring."""
        df = pd.DataFrame({
            'supplier_id': [1, 2, 3],
            'supplier': ['A', 'B', 'C'],
            'total_orders': [100, 150, 120],
            'total_cost': [50000, 75000, 60000],
            'total_savings': [4000, 5000, 5500],
            'avg_savings_percentage': [8.0, 7.5, 9.0],
            'avg_lead_time_days': [10.0, 12.0, 9.0],
            'avg_defect_rate': [5.0, 8.0, 3.0],
            'compliance_rate': [95.0, 85.0, 98.0],
            'savings_score': [8.0, 7.5, 9.0],
            'quality_score': [95.0, 92.0, 97.0],
            'lead_time_score': [90.0, 88.0, 91.0],
            'compliance_score': [95.0, 85.0, 98.0],
            'data_completeness_pct': [90.0, 93.0, 95.0]
        })
        
        scorer = SupplierScorer()
        result = scorer.score_suppliers(df)
        
        assert 'supplier_score' in result.columns
        assert 'supplier_rank' in result.columns
        assert 'performance_category' in result.columns
        assert len(result) == 3
        assert result['supplier_score'].min() >= 0
        assert result['supplier_score'].max() <= 100
        assert result['supplier_rank'].min() == 1
        assert set(result['performance_category'].unique()).issubset({'Excellent', 'Good', 'Average', 'Poor'})


class TestPriceAnomalyDetector:
    """Test price anomaly detection."""
    
    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = PriceAnomalyDetector(contamination=0.05)
        
        assert detector.contamination == 0.05
        assert detector.model is None
    
    def test_select_features(self):
        """Test feature selection."""
        df = pd.DataFrame({
            'negotiated_price': np.random.rand(100) * 100,
            'discount_pct': np.random.rand(100) * 20,
            'order_value': np.random.rand(100) * 10000,
            'price_deviation_from_avg': np.random.randn(100) * 10,
            'log_quantity': np.random.rand(100) * 5
        })
        
        detector = PriceAnomalyDetector()
        features = detector.select_features(df)
        
        assert len(features) >= 3, "Should select at least 3 features"
        assert 'negotiated_price' in features
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        # Create sample data with some outliers
        np.random.seed(42)
        normal_prices = np.random.normal(50, 10, 95)
        outlier_prices = np.array([150, 5, 200, 3, 180])  # Obvious outliers
        
        df = pd.DataFrame({
            'po_id': [f'PO-{i:05d}' for i in range(100)],
            'supplier': ['SupplierA'] * 100,
            'item_category': ['Electronics'] * 100,
            'order_date': pd.date_range('2023-01-01', periods=100, freq='D'),
            'quantity': np.random.randint(10, 1000, 100),
            'unit_price': np.concatenate([normal_prices, outlier_prices]),
            'negotiated_price': np.concatenate([normal_prices, outlier_prices]),
            'total_cost': np.concatenate([normal_prices, outlier_prices]) * 10,
            'savings_percentage': np.random.rand(100) * 10,
            'discount_pct': np.random.rand(100) * 5,
            'order_value': np.random.rand(100) * 10000,
            'price_deviation_from_avg': np.concatenate([
                np.random.randn(95) * 5,
                np.array([100, -45, 120, -48, 110])
            ]),
            'log_quantity': np.log1p(np.random.randint(10, 1000, 100)),
            'price_deviation_from_rolling': np.random.randn(100) * 5
        })
        
        detector = PriceAnomalyDetector(contamination=0.05)
        result = detector.detect_anomalies(df)
        
        assert 'anomaly_status' in result.columns
        assert 'anomaly_score' in result.columns
        assert 'price_level' in result.columns
        assert set(result['anomaly_status'].unique()).issubset({'Normal', 'Anomaly'})
        
        anomalies = result[result['anomaly_status'] == 'Anomaly']
        assert len(anomalies) > 0, "Should detect some anomalies"
        assert len(anomalies) / len(result) <= 0.15, "Anomaly rate should be reasonable"


class TestDemandForecaster:
    """Test demand forecasting."""
    
    def test_forecaster_initialization(self):
        """Test forecaster initialization."""
        forecaster = DemandForecaster(forecast_periods=3)
        
        assert forecaster.forecast_periods == 3
        assert forecaster.models == {}
    
    def test_prepare_series(self):
        """Test time series preparation."""
        dates = pd.date_range('2022-01-01', periods=24, freq='MS')
        df = pd.DataFrame({
            'total_quantity': np.random.randint(20000, 50000, 24)
        }, index=dates)
        
        forecaster = DemandForecaster()
        series = forecaster.prepare_series(df, 'total_quantity')
        
        assert isinstance(series, pd.Series)
        assert len(series) == 24
        assert (series >= 0).all(), "No negative values should exist"
    
    def test_split_time_series(self):
        """Test time-based split (NOT random shuffle)."""
        dates = pd.date_range('2022-01-01', periods=24, freq='MS')
        series = pd.Series(np.random.rand(24) * 1000, index=dates)
        
        forecaster = DemandForecaster()
        train, test = forecaster.split_series(series, test_size=3)
        
        assert len(train) == 21
        assert len(test) == 3
        assert train.index.max() < test.index.min(), "Train should be before test (time-based split)"
    
    def test_forecast_overall(self):
        """Test overall forecasting."""
        # Create sample time series
        dates = pd.date_range('2022-01-01', periods=24, freq='MS')
        df = pd.DataFrame({
            'month_date': dates,
            'total_quantity': np.random.randint(20000, 50000, 24) + np.arange(24) * 500  # Add trend
        })
        df = df.set_index('month_date')
        
        forecaster = DemandForecaster(forecast_periods=3)
        forecast_df, metrics = forecaster.forecast_overall(df, test_size=3)
        
        assert len(forecast_df) == 3, "Should generate 3 forecasts"
        assert 'predicted_quantity' in forecast_df.columns
        assert 'lower_bound' in forecast_df.columns
        assert 'upper_bound' in forecast_df.columns
        assert 'MAE' in metrics
        assert 'RMSE' in metrics
        assert metrics['MAE'] > 0
        assert (forecast_df['predicted_quantity'] >= 0).all()


class TestDataQualityRequirements:
    """Test critical data quality requirements."""
    
    def test_missing_defects_not_zero(self):
        """Test that missing defective_units are NOT treated as zero defects."""
        df = pd.DataFrame({
            'defective_units': [10.0, np.nan, 5.0, np.nan, 2.0],
            'quantity': [100, 100, 100, 100, 100]
        })
        
        # Calculate defect rate excluding NaN
        df['defect_rate'] = (df['defective_units'] / df['quantity']) * 100
        
        # Missing values should remain NaN, not become 0
        assert df['defect_rate'].isna().sum() == 2, "Missing values should remain NaN"
        assert df['defect_rate'].notna().sum() == 3
    
    def test_missing_delivery_not_success(self):
        """Test that missing delivery_date are NOT treated as successful delivery."""
        df = pd.DataFrame({
            'order_date': pd.date_range('2023-01-01', periods=5),
            'delivery_date': [
                pd.Timestamp('2023-01-10'),
                pd.NaT,
                pd.Timestamp('2023-01-15'),
                pd.NaT,
                pd.Timestamp('2023-01-20')
            ]
        })
        
        # Calculate lead time only for non-null delivery dates
        df['lead_time'] = (df['delivery_date'] - df['order_date']).dt.days
        
        # Missing delivery dates should result in NaN lead time, not 0
        assert df['lead_time'].isna().sum() == 2, "Missing delivery dates should result in NaN lead time"
        assert df['lead_time'].notna().sum() == 3
    
    def test_time_series_not_shuffled(self):
        """Test that time series are NOT randomly shuffled."""
        dates = pd.date_range('2022-01-01', periods=12, freq='MS')
        series = pd.Series(range(12), index=dates)
        
        forecaster = DemandForecaster()
        train, test = forecaster.split_series(series, test_size=3)
        
        # Check that train comes before test
        assert train.index.max() < test.index.min(), "Time series split should be time-ordered, not shuffled"
        
        # Check that values are sequential
        assert list(train.values) == list(range(9)), "Train set should be first 9 values in order"
        assert list(test.values) == [9, 10, 11], "Test set should be last 3 values in order"


def test_module_4_integration():
    """Integration test for complete Module 4 pipeline."""
    try:
        loader = MLDataLoader()
        
        # Load data
        purchase_orders = loader.load_purchase_orders()
        supplier_aggregates = loader.load_supplier_aggregates()
        
        assert len(purchase_orders) == 777, "Should load 777 purchase orders"
        assert len(supplier_aggregates) == 5, "Should have 5 suppliers"
        
        # Preprocessing
        prep = MLPreprocessor()
        supplier_features = prep.prepare_supplier_features(supplier_aggregates)
        
        # Scoring
        scorer = SupplierScorer()
        scores = scorer.score_suppliers(supplier_features)
        
        assert len(scores) == 5
        assert scores['supplier_rank'].min() == 1
        assert scores['supplier_rank'].max() == 5
        
        print("✓ Module 4 integration test passed")
        
    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
