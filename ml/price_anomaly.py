"""
Price Anomaly Detection Module

Uses Isolation Forest algorithm to detect unusual procurement prices.

Why Isolation Forest:
- Works well for high-dimensional data
- No assumptions about data distribution
- Naturally handles multivariate anomalies
- Doesn't require labeled anomalous examples
- Effective at isolating outliers in procurement pricing patterns

The model identifies orders with unusual price characteristics compared to
historical patterns for the same supplier-category combination.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple
from sklearn.ensemble import IsolationForest
import pickle

logger = logging.getLogger(__name__)


class PriceAnomalyDetector:
    """Detects price anomalies using Isolation Forest."""
    
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies (default 5%)
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model = None
        self.feature_cols = None
        
        logger.info(f"Initialized PriceAnomalyDetector with contamination={contamination}")
    
    def select_features(self, df: pd.DataFrame) -> list:
        """
        Select features for anomaly detection.
        
        Args:
            df: DataFrame with prepared features
            
        Returns:
            List of feature column names
        """
        # Core features for price anomaly detection
        feature_candidates = [
            'negotiated_price',      # Actual price paid
            'discount_pct',          # How much was discounted
            'order_value',           # Total order value
            'price_deviation_from_avg',  # Deviation from supplier-category average
            'log_quantity',          # Quantity (log-transformed)
            'price_deviation_from_rolling',  # Deviation from rolling average
        ]
        
        # Select features that exist and have enough data
        available_features = [col for col in feature_candidates if col in df.columns]
        
        # Check for sufficient non-null data
        features = []
        for col in available_features:
            non_null_pct = df[col].notna().sum() / len(df) * 100
            if non_null_pct >= 90:  # At least 90% complete
                features.append(col)
                logger.info(f"Selected feature: {col} ({non_null_pct:.1f}% complete)")
            else:
                logger.warning(f"Skipped feature: {col} ({non_null_pct:.1f}% complete)")
        
        if len(features) < 3:
            raise ValueError(f"Insufficient features for anomaly detection. Need at least 3, got {len(features)}")
        
        self.feature_cols = features
        return features
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for anomaly detection.
        
        Handles missing values by excluding records with nulls in critical features.
        
        Args:
            df: DataFrame with features
            
        Returns:
            Clean DataFrame ready for model
        """
        df = df.copy()
        
        # Drop records with missing values in selected features
        original_count = len(df)
        df = df.dropna(subset=self.feature_cols)
        
        if len(df) < original_count:
            logger.info(f"Dropped {original_count - len(df)} records with missing feature values")
        
        logger.info(f"Prepared {len(df)} records for anomaly detection")
        
        return df
    
    def fit_detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit Isolation Forest and detect anomalies.
        
        Args:
            df: DataFrame with prepared features
            
        Returns:
            DataFrame with anomaly predictions
        """
        logger.info("Fitting Isolation Forest model...")
        
        # Extract features
        X = df[self.feature_cols].values
        
        # Fit model
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1
        )
        
        # Predict: -1 for anomalies, 1 for normal
        predictions = self.model.fit_predict(X)
        
        # Get anomaly scores (more negative = more anomalous)
        anomaly_scores = self.model.score_samples(X)
        
        # Add to dataframe
        df['anomaly_prediction'] = predictions
        df['anomaly_score'] = anomaly_scores
        
        # Convert to interpretable labels
        df['anomaly_status'] = df['anomaly_prediction'].map({
            1: 'Normal',
            -1: 'Anomaly'
        })
        
        # Count anomalies
        anomaly_count = (predictions == -1).sum()
        anomaly_pct = (anomaly_count / len(predictions)) * 100
        
        logger.info(f"Detected {anomaly_count} anomalies ({anomaly_pct:.2f}% of {len(df)} records)")
        
        return df
    
    def classify_anomaly_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify anomalies as high-price or low-price.
        
        Uses price deviation from average to determine direction.
        
        Args:
            df: DataFrame with anomaly predictions
            
        Returns:
            DataFrame with anomaly type classification
        """
        df = df.copy()
        
        def get_price_level(row):
            if row['anomaly_status'] == 'Normal':
                return 'Normal'
            
            # Use price deviation to determine if high or low
            if 'price_deviation_from_avg' in df.columns and pd.notna(row['price_deviation_from_avg']):
                if row['price_deviation_from_avg'] > 0:
                    return 'High'
                elif row['price_deviation_from_avg'] < 0:
                    return 'Low'
            
            # Fallback: compare to median
            median_price = df[df['supplier'] == row['supplier']]['negotiated_price'].median()
            if row['negotiated_price'] > median_price:
                return 'High'
            elif row['negotiated_price'] < median_price:
                return 'Low'
            
            return 'Unknown'
        
        df['price_level'] = df.apply(get_price_level, axis=1)
        
        # Log distribution
        price_level_counts = df[df['anomaly_status'] == 'Anomaly']['price_level'].value_counts()
        logger.info("Anomaly price level distribution:")
        for level, count in price_level_counts.items():
            logger.info(f"  {level}: {count}")
        
        return df
    
    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Complete anomaly detection pipeline.
        
        Args:
            df: DataFrame with prepared features from preprocessing
            
        Returns:
            DataFrame with anomaly detection results
        """
        logger.info(f"Running anomaly detection on {len(df)} purchase orders...")
        
        # Step 1: Select features
        self.select_features(df)
        
        # Step 2: Prepare data
        df_clean = self.prepare_data(df)
        
        # Step 3: Fit and detect
        df_results = self.fit_detect(df_clean)
        
        # Step 4: Classify anomaly types
        df_results = self.classify_anomaly_type(df_results)
        
        # Step 5: Select output columns
        output_cols = [
            'po_id',
            'supplier',
            'item_category',
            'order_date',
            'quantity',
            'unit_price',
            'negotiated_price',
            'total_cost',
            'savings_percentage',
            'anomaly_score',
            'anomaly_status',
            'price_level'
        ]
        
        result = df_results[[col for col in output_cols if col in df_results.columns]].copy()
        
        # Round numeric columns
        result['unit_price'] = result['unit_price'].round(2)
        result['negotiated_price'] = result['negotiated_price'].round(2)
        result['total_cost'] = result['total_cost'].round(2)
        result['anomaly_score'] = result['anomaly_score'].round(4)
        
        logger.info("Anomaly detection complete!")
        
        return result
    
    def get_anomaly_summary(self, result_df: pd.DataFrame) -> dict:
        """
        Generate summary statistics for anomaly detection.
        
        Args:
            result_df: DataFrame with detection results
            
        Returns:
            Dictionary with summary statistics
        """
        anomalies = result_df[result_df['anomaly_status'] == 'Anomaly']
        
        summary = {
            'total_records': len(result_df),
            'total_anomalies': len(anomalies),
            'anomaly_percentage': (len(anomalies) / len(result_df) * 100) if len(result_df) > 0 else 0,
            'anomaly_score_range': (result_df['anomaly_score'].min(), result_df['anomaly_score'].max()),
            'anomaly_by_supplier': anomalies['supplier'].value_counts().to_dict() if len(anomalies) > 0 else {},
            'anomaly_by_category': anomalies['item_category'].value_counts().to_dict() if len(anomalies) > 0 else {},
            'anomaly_by_price_level': anomalies['price_level'].value_counts().to_dict() if len(anomalies) > 0 else {},
            'high_price_anomalies': len(anomalies[anomalies['price_level'] == 'High']),
            'low_price_anomalies': len(anomalies[anomalies['price_level'] == 'Low']),
        }
        
        return summary
    
    def get_top_anomalies(self, result_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """
        Get top N most anomalous records.
        
        Args:
            result_df: DataFrame with detection results
            n: Number of top anomalies to return
            
        Returns:
            DataFrame with top N anomalies
        """
        anomalies = result_df[result_df['anomaly_status'] == 'Anomaly'].copy()
        
        # Sort by anomaly score (most negative = most anomalous)
        top_anomalies = anomalies.nsmallest(n, 'anomaly_score')
        
        return top_anomalies
    
    def save_model(self, filepath: str):
        """
        Save trained model to file.
        
        Args:
            filepath: Path to save model
        """
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        model_data = {
            'model': self.model,
            'feature_cols': self.feature_cols,
            'contamination': self.contamination,
            'random_state': self.random_state
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Load trained model from file.
        
        Args:
            filepath: Path to load model from
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_cols = model_data['feature_cols']
        self.contamination = model_data['contamination']
        self.random_state = model_data['random_state']
        
        logger.info(f"Model loaded from {filepath}")


def detect_price_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> Tuple[pd.DataFrame, dict]:
    """
    Convenience function to run complete anomaly detection pipeline.
    
    Args:
        df: DataFrame with prepared features
        contamination: Expected proportion of anomalies
        
    Returns:
        Tuple of (results_df, summary_dict)
    """
    detector = PriceAnomalyDetector(contamination=contamination)
    
    results = detector.detect_anomalies(df)
    summary = detector.get_anomaly_summary(results)
    
    return results, summary
