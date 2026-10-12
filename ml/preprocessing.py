"""
ML Preprocessing Module
Handles data preparation, missing value handling, and feature engineering.

IMPORTANT: Missing delivery dates and defective units are NOT treated as zeros.
They are either excluded from calculations or explicitly marked as missing.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Optional
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class MLPreprocessor:
    """Preprocesses procurement data for ML models."""
    
    def __init__(self):
        """Initialize the preprocessor."""
        self.scalers = {}
        
    def prepare_supplier_features(self, supplier_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for supplier performance scoring.
        
        IMPORTANT: Missing values are handled carefully:
        - avg_lead_time_days: Only calculated from orders with delivery dates
        - avg_defect_rate: Only calculated from orders with defect data
        - Missing data does NOT mean zero/good performance
        
        Args:
            supplier_df: DataFrame with supplier aggregates
            
        Returns:
            DataFrame with engineered features for scoring
        """
        logger.info("Preparing supplier features for scoring...")
        
        df = supplier_df.copy()
        
        # Feature 1: Savings performance (higher is better)
        # Normalized savings percentage
        df['savings_score'] = df['avg_savings_percentage']
        
        # Feature 2: Lead time performance (lower is better, so invert)
        # Only use if we have delivery data
        df['lead_time_score'] = np.where(
            df['avg_lead_time_days'].notna(),
            100 - df['avg_lead_time_days'],  # Invert so lower lead time = higher score
            np.nan
        )
        
        # Feature 3: Quality performance (lower defect rate is better, so invert)
        # Only use if we have defect data
        df['quality_score'] = np.where(
            df['avg_defect_rate'].notna(),
            100 - df['avg_defect_rate'],  # Invert so lower defect = higher score
            np.nan
        )
        
        # Feature 4: Compliance rate (already percentage, higher is better)
        df['compliance_score'] = df['compliance_rate']
        
        # Feature 5: Data availability score
        # Reward suppliers with more complete data
        df['data_completeness_pct'] = (
            (df['orders_with_delivery'] + df['orders_with_defect_data']) / 
            (2 * df['total_orders']) * 100
        )
        
        # Log feature statistics
        logger.info(f"Feature ranges:")
        logger.info(f"  Savings: {df['savings_score'].min():.2f} - {df['savings_score'].max():.2f}")
        logger.info(f"  Lead time: {df['lead_time_score'].min():.2f} - {df['lead_time_score'].max():.2f}")
        logger.info(f"  Quality: {df['quality_score'].dropna().min():.2f} - {df['quality_score'].dropna().max():.2f}")
        logger.info(f"  Compliance: {df['compliance_score'].min():.2f} - {df['compliance_score'].max():.2f}")
        logger.info(f"  Data completeness: {df['data_completeness_pct'].min():.2f} - {df['data_completeness_pct'].max():.2f}")
        
        return df
    
    def prepare_anomaly_features(self, po_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for price anomaly detection.
        
        Args:
            po_df: DataFrame with purchase orders
            
        Returns:
            DataFrame with features for anomaly detection
        """
        logger.info("Preparing features for price anomaly detection...")
        
        df = po_df.copy()
        
        # Feature engineering for anomaly detection
        
        # 1. Price per unit
        df['price_per_unit'] = df['negotiated_price']
        
        # 2. Discount percentage (unit_price - negotiated_price) / unit_price
        df['discount_pct'] = ((df['unit_price'] - df['negotiated_price']) / df['unit_price']) * 100
        
        # 3. Total order value
        df['order_value'] = df['total_cost']
        
        # 4. Price volatility: deviation from supplier-category average
        supplier_category_avg = df.groupby(['supplier', 'item_category'])['negotiated_price'].transform('mean')
        df['price_deviation_from_avg'] = ((df['negotiated_price'] - supplier_category_avg) / supplier_category_avg) * 100
        
        # 5. Quantity-based features
        df['log_quantity'] = np.log1p(df['quantity'])
        
        # 6. Temporal features
        df['month'] = df['order_date'].dt.month
        df['quarter'] = df['order_date'].dt.quarter
        df['year'] = df['order_date'].dt.year
        
        # 7. Historical price comparison (rolling average)
        df = df.sort_values('order_date')
        df['price_rolling_mean'] = df.groupby(['supplier', 'item_category'])['negotiated_price'].transform(
            lambda x: x.rolling(window=5, min_periods=1).mean()
        )
        df['price_deviation_from_rolling'] = ((df['negotiated_price'] - df['price_rolling_mean']) / 
                                               df['price_rolling_mean']) * 100
        
        logger.info(f"Prepared {len(df)} records for anomaly detection")
        logger.info(f"Feature dimensions: {df.shape[1]} columns")
        
        return df
    
    def prepare_time_series(self, ts_df: pd.DataFrame, freq: str = 'MS') -> pd.DataFrame:
        """
        Prepare time series data for forecasting.
        
        Args:
            ts_df: DataFrame with time series data
            freq: Frequency string (MS = Month Start)
            
        Returns:
            DataFrame with properly indexed time series
        """
        logger.info("Preparing time series for forecasting...")
        
        df = ts_df.copy()
        
        # Set datetime index
        if 'month_date' in df.columns:
            df = df.set_index('month_date')
        
        # Sort by index
        df = df.sort_index()
        
        # Fill any missing months with zeros (genuine missing data, not observed orders)
        # Create complete date range
        date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
        
        # Reindex to fill missing months
        if 'item_category' in df.columns:
            # Category-level: need to handle each category separately
            categories = df['item_category'].unique()
            dfs = []
            
            for category in categories:
                cat_df = df[df['item_category'] == category].copy()
                cat_df = cat_df.reindex(date_range, fill_value=0)
                cat_df['item_category'] = category
                dfs.append(cat_df)
            
            df = pd.concat(dfs, axis=0).sort_index()
        else:
            # Overall: simple reindex
            df = df.reindex(date_range, fill_value=0)
        
        logger.info(f"Time series range: {df.index.min()} to {df.index.max()}")
        logger.info(f"Total periods: {len(df.index.unique())}")
        
        return df
    
    def split_time_series(
        self, 
        df: pd.DataFrame, 
        test_size: int = 3
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split time series into train and test sets.
        
        IMPORTANT: Uses time-based split, NOT random shuffling.
        
        Args:
            df: Time series DataFrame
            test_size: Number of periods to use for testing
            
        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"Splitting time series with test_size={test_size}...")
        
        # Sort by date
        df = df.sort_index()
        
        # Time-based split (last N periods for test)
        split_point = len(df) - test_size
        
        train_df = df.iloc[:split_point].copy()
        test_df = df.iloc[split_point:].copy()
        
        logger.info(f"Train set: {len(train_df)} periods ({train_df.index.min()} to {train_df.index.max()})")
        logger.info(f"Test set: {len(test_df)} periods ({test_df.index.min()} to {test_df.index.max()})")
        
        return train_df, test_df
    
    def normalize_features(
        self, 
        df: pd.DataFrame, 
        feature_cols: list,
        scaler_name: str = 'default',
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Normalize features using StandardScaler.
        
        Args:
            df: DataFrame with features
            feature_cols: List of columns to normalize
            scaler_name: Name for storing/retrieving scaler
            fit: Whether to fit scaler (True for train, False for test)
            
        Returns:
            DataFrame with normalized features
        """
        df = df.copy()
        
        if fit:
            scaler = StandardScaler()
            df[feature_cols] = scaler.fit_transform(df[feature_cols])
            self.scalers[scaler_name] = scaler
            logger.info(f"Fitted and transformed {len(feature_cols)} features")
        else:
            if scaler_name not in self.scalers:
                raise ValueError(f"Scaler '{scaler_name}' not found. Must fit before transform.")
            scaler = self.scalers[scaler_name]
            df[feature_cols] = scaler.transform(df[feature_cols])
            logger.info(f"Transformed {len(feature_cols)} features using existing scaler")
        
        return df
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame, 
        strategy: str = 'exclude'
    ) -> pd.DataFrame:
        """
        Handle missing values according to specified strategy.
        
        IMPORTANT: 
        - Missing defective_units does NOT mean zero defects
        - Missing delivery_date does NOT mean successful delivery
        - Default strategy is to EXCLUDE records with missing critical data
        
        Args:
            df: DataFrame with potential missing values
            strategy: 'exclude', 'mark', or 'impute'
            
        Returns:
            DataFrame with missing values handled
        """
        logger.info(f"Handling missing values with strategy: {strategy}")
        
        original_count = len(df)
        
        if strategy == 'exclude':
            # Exclude records with missing values
            # (This is appropriate for models that can't handle NaN)
            df = df.dropna()
            logger.info(f"Excluded {original_count - len(df)} records with missing values")
            
        elif strategy == 'mark':
            # Mark missing values with a flag (for models that can use this info)
            df['has_missing_delivery'] = df['delivery_date'].isna()
            df['has_missing_defects'] = df['defective_units'].isna()
            logger.info("Added missing value flags")
            
        elif strategy == 'impute':
            # This should be used carefully and only when appropriate
            logger.warning("Imputation strategy should only be used with explicit justification")
            # Do not impute by default
            
        return df
    
    def get_feature_importance_data(self, df: pd.DataFrame) -> dict:
        """
        Calculate feature statistics for importance analysis.
        
        Args:
            df: DataFrame with features
            
        Returns:
            Dictionary with feature statistics
        """
        stats = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'missing_pct': float(df[col].isna().sum() / len(df) * 100)
            }
        
        return stats
