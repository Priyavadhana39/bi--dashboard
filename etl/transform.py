"""
Transform Module
Handles data transformation, cleaning, and derived column creation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms and cleans procurement data."""
    
    def __init__(self):
        """Initialize the DataTransformer."""
        self.transformation_stats = {
            'duplicates_removed': 0,
            'invalid_records': [],
            'missing_values_before': {},
            'missing_values_after': {},
            'records_before': 0,
            'records_after': 0
        }
    
    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names to snake_case.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized column names
        """
        logger.info("Standardizing column names to snake_case...")
        
        # Convert to snake_case
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        logger.info(f"Standardized columns: {df.columns.tolist()}")
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove exact duplicate records.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with duplicates removed
        """
        logger.info("Checking for duplicate records...")
        
        initial_count = len(df)
        df = df.drop_duplicates()
        final_count = len(df)
        
        duplicates_removed = initial_count - final_count
        self.transformation_stats['duplicates_removed'] = duplicates_removed
        
        if duplicates_removed > 0:
            logger.warning(f"Removed {duplicates_removed} duplicate records")
        else:
            logger.info("No duplicate records found")
        
        return df
    
    def convert_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert date columns to datetime format.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with converted date columns
        """
        logger.info("Converting date columns to datetime format...")
        
        date_columns = ['order_date', 'delivery_date']
        
        for col in date_columns:
            if col in df.columns:
                # Convert to datetime, coerce errors to NaT (Not a Time)
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
                null_count = df[col].isna().sum()
                if null_count > 0:
                    logger.info(f"Column '{col}': {null_count} missing/invalid dates")
        
        logger.info("Date columns converted successfully")
        return df
    
    def convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert numeric columns to appropriate numeric types.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with converted numeric columns
        """
        logger.info("Converting numeric columns...")
        
        numeric_columns = {
            'quantity': 'int64',
            'unit_price': 'float64',
            'negotiated_price': 'float64',
            'defective_units': 'float64'  # Float to allow NaN for missing values
        }
        
        for col, dtype in numeric_columns.items():
            if col in df.columns:
                # Convert to numeric, coerce errors to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # For quantity, convert to int (after validation)
                if col == 'quantity':
                    # Fill NaN temporarily for conversion
                    df[col] = df[col].fillna(-1).astype('int64')
        
        logger.info("Numeric columns converted successfully")
        return df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data for logical consistency.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with validation flags
        """
        logger.info("Validating data for logical consistency...")
        
        invalid_records = []
        
        # Check for negative quantities
        if 'quantity' in df.columns:
            negative_qty = df[df['quantity'] < 0]
            if len(negative_qty) > 0:
                logger.warning(f"Found {len(negative_qty)} records with negative quantity")
                invalid_records.extend(negative_qty.index.tolist())
        
        # Check for negative prices
        if 'unit_price' in df.columns:
            negative_price = df[df['unit_price'] < 0]
            if len(negative_price) > 0:
                logger.warning(f"Found {len(negative_price)} records with negative unit_price")
                invalid_records.extend(negative_price.index.tolist())
        
        if 'negotiated_price' in df.columns:
            negative_negotiated = df[df['negotiated_price'] < 0]
            if len(negative_negotiated) > 0:
                logger.warning(f"Found {len(negative_negotiated)} records with negative negotiated_price")
                invalid_records.extend(negative_negotiated.index.tolist())
        
        # Check for defective_units > quantity
        if 'defective_units' in df.columns and 'quantity' in df.columns:
            invalid_defects = df[df['defective_units'] > df['quantity']]
            if len(invalid_defects) > 0:
                logger.warning(f"Found {len(invalid_defects)} records where defective_units > quantity")
                invalid_records.extend(invalid_defects.index.tolist())
        
        # Store unique invalid record indices
        self.transformation_stats['invalid_records'] = list(set(invalid_records))
        
        if len(invalid_records) > 0:
            logger.info(f"Total invalid records identified: {len(set(invalid_records))}")
        else:
            logger.info("All records passed validation checks")
        
        return df
    
    def standardize_categorical_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize categorical column values.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized categorical values
        """
        logger.info("Standardizing categorical values...")
        
        # Standardize supplier names (trim whitespace, consistent casing)
        if 'supplier' in df.columns:
            df['supplier'] = df['supplier'].str.strip()
            unique_suppliers = df['supplier'].nunique()
            logger.info(f"Standardized {unique_suppliers} unique suppliers")
        
        # Standardize item_category
        if 'item_category' in df.columns:
            df['item_category'] = df['item_category'].str.strip()
            unique_categories = df['item_category'].nunique()
            logger.info(f"Standardized {unique_categories} unique item categories")
        
        # Standardize order_status
        if 'order_status' in df.columns:
            df['order_status'] = df['order_status'].str.strip()
            unique_statuses = df['order_status'].nunique()
            logger.info(f"Standardized {unique_statuses} unique order statuses")
        
        # Standardize compliance (Yes/No to boolean-like)
        if 'compliance' in df.columns:
            df['compliance'] = df['compliance'].str.strip()
            logger.info("Standardized compliance values")
        
        logger.info("Categorical values standardized successfully")
        return df
    
    def create_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create derived columns from existing data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with derived columns added
        """
        logger.info("Creating derived columns...")
        
        # 1. Total Cost = quantity × negotiated_price
        if 'quantity' in df.columns and 'negotiated_price' in df.columns:
            df['total_cost'] = df['quantity'] * df['negotiated_price']
            logger.info("Created 'total_cost' column")
        
        # 2. Savings = (unit_price - negotiated_price) × quantity
        if 'unit_price' in df.columns and 'negotiated_price' in df.columns and 'quantity' in df.columns:
            df['savings'] = (df['unit_price'] - df['negotiated_price']) * df['quantity']
            logger.info("Created 'savings' column")
        
        # 3. Savings Percentage = savings / (unit_price × quantity) × 100
        if 'unit_price' in df.columns and 'quantity' in df.columns and 'savings' in df.columns:
            total_original_cost = df['unit_price'] * df['quantity']
            # Avoid division by zero
            df['savings_percentage'] = np.where(
                total_original_cost > 0,
                (df['savings'] / total_original_cost) * 100,
                0
            )
            logger.info("Created 'savings_percentage' column")
        
        # 4. Defect Rate = defective_units / quantity × 100 (only when defective_units is available)
        if 'defective_units' in df.columns and 'quantity' in df.columns:
            df['defect_rate'] = np.where(
                (df['defective_units'].notna()) & (df['quantity'] > 0),
                (df['defective_units'] / df['quantity']) * 100,
                np.nan
            )
            logger.info("Created 'defect_rate' column")
        
        # 5. Lead Time Days = delivery_date - order_date (only when delivery_date is available)
        if 'delivery_date' in df.columns and 'order_date' in df.columns:
            df['lead_time_days'] = (df['delivery_date'] - df['order_date']).dt.days
            logger.info("Created 'lead_time_days' column")
        
        # 6. Order Year
        if 'order_date' in df.columns:
            df['order_year'] = df['order_date'].dt.year
            logger.info("Created 'order_year' column")
        
        # 7. Order Month
        if 'order_date' in df.columns:
            df['order_month'] = df['order_date'].dt.month
            logger.info("Created 'order_month' column")
        
        # 8. Order Quarter
        if 'order_date' in df.columns:
            df['order_quarter'] = df['order_date'].dt.quarter
            logger.info("Created 'order_quarter' column")
        
        logger.info("All derived columns created successfully")
        return df
    
    def track_missing_values(self, df: pd.DataFrame, stage: str) -> None:
        """
        Track missing values at different stages.
        
        Args:
            df: Input DataFrame
            stage: 'before' or 'after' transformation
        """
        missing_counts = df.isna().sum().to_dict()
        
        if stage == 'before':
            self.transformation_stats['missing_values_before'] = missing_counts
        elif stage == 'after':
            self.transformation_stats['missing_values_after'] = missing_counts
    
    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Execute complete transformation pipeline.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (transformed DataFrame, transformation statistics)
        """
        logger.info("Starting data transformation pipeline...")
        
        self.transformation_stats['records_before'] = len(df)
        
        # Track missing values before transformation
        self.track_missing_values(df, 'before')
        
        # Step 1: Standardize column names
        df = self.standardize_column_names(df)
        
        # Step 2: Remove duplicates
        df = self.remove_duplicates(df)
        
        # Step 3: Convert date columns
        df = self.convert_date_columns(df)
        
        # Step 4: Convert numeric columns
        df = self.convert_numeric_columns(df)
        
        # Step 5: Validate data
        df = self.validate_data(df)
        
        # Step 6: Standardize categorical values
        df = self.standardize_categorical_values(df)
        
        # Step 7: Create derived columns
        df = self.create_derived_columns(df)
        
        # Track missing values after transformation
        self.track_missing_values(df, 'after')
        
        self.transformation_stats['records_after'] = len(df)
        
        logger.info("Data transformation pipeline completed successfully")
        
        return df, self.transformation_stats
