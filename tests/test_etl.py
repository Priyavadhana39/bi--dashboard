"""
Unit Tests for ETL Components
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from etl.extract import DataExtractor
from etl.transform import DataTransformer
from etl.validate import DataValidator


class TestDataExtractor(unittest.TestCase):
    """Test cases for DataExtractor."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary CSV file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = os.path.join(self.temp_dir, "test_data.csv")
        
        # Create sample data
        test_data = {
            'PO_ID': ['PO-00001', 'PO-00002'],
            'Supplier': ['Alpha_Inc', 'Beta_Supplies'],
            'Order_Date': ['2023-01-01', '2023-01-02'],
            'Delivery_Date': ['2023-01-10', '2023-01-12'],
            'Item_Category': ['Office Supplies', 'Electronics'],
            'Order_Status': ['Delivered', 'Pending'],
            'Quantity': [100, 200],
            'Unit_Price': [10.0, 20.0],
            'Negotiated_Price': [9.0, 18.0],
            'Defective_Units': [5.0, 10.0],
            'Compliance': ['Yes', 'Yes']
        }
        
        df = pd.DataFrame(test_data)
        df.to_csv(self.test_csv_path, index=False)
        
        self.extractor = DataExtractor(self.test_csv_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        os.rmdir(self.temp_dir)
    
    def test_validate_file_exists(self):
        """Test file existence validation."""
        self.assertTrue(self.extractor.validate_file_exists())
    
    def test_validate_file_not_exists(self):
        """Test validation fails for non-existent file."""
        extractor = DataExtractor("nonexistent.csv")
        self.assertFalse(extractor.validate_file_exists())
    
    def test_extract_data(self):
        """Test data extraction."""
        df, metadata = self.extractor.extract()
        
        self.assertEqual(len(df), 2)
        self.assertEqual(metadata['total_records'], 2)
        self.assertEqual(metadata['total_columns'], 11)
        self.assertIn('PO_ID', metadata['columns'])


class TestDataTransformer(unittest.TestCase):
    """Test cases for DataTransformer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.transformer = DataTransformer()
        
        # Create sample DataFrame
        self.sample_data = pd.DataFrame({
            'PO_ID': ['PO-00001', 'PO-00002', 'PO-00001'],  # Duplicate for testing
            'Supplier': ['Alpha_Inc', 'Beta_Supplies', 'Alpha_Inc'],
            'Order_Date': ['2023-01-01', '2023-01-02', '2023-01-01'],
            'Delivery_Date': ['2023-01-10', '2023-01-12', '2023-01-10'],
            'Item_Category': ['Office Supplies', 'Electronics', 'Office Supplies'],
            'Order_Status': ['Delivered', 'Pending', 'Delivered'],
            'Quantity': [100, 200, 100],
            'Unit_Price': [10.0, 20.0, 10.0],
            'Negotiated_Price': [9.0, 18.0, 9.0],
            'Defective_Units': [5.0, 10.0, 5.0],
            'Compliance': ['Yes', 'Yes', 'Yes']
        })
    
    def test_standardize_column_names(self):
        """Test column name standardization."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        
        expected_columns = ['po_id', 'supplier', 'order_date', 'delivery_date',
                          'item_category', 'order_status', 'quantity',
                          'unit_price', 'negotiated_price', 'defective_units',
                          'compliance']
        
        self.assertEqual(df.columns.tolist(), expected_columns)
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.remove_duplicates(df)
        
        self.assertEqual(len(df), 2)  # Should have 2 unique records
        self.assertEqual(self.transformer.transformation_stats['duplicates_removed'], 1)
    
    def test_convert_date_columns(self):
        """Test date conversion."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.convert_date_columns(df)
        
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['order_date']))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['delivery_date']))
    
    def test_convert_numeric_columns(self):
        """Test numeric conversion."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.convert_numeric_columns(df)
        
        self.assertTrue(pd.api.types.is_integer_dtype(df['quantity']))
        self.assertTrue(pd.api.types.is_float_dtype(df['unit_price']))
        self.assertTrue(pd.api.types.is_float_dtype(df['negotiated_price']))
        self.assertTrue(pd.api.types.is_float_dtype(df['defective_units']))
    
    def test_total_cost_calculation(self):
        """Test total cost calculation."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.convert_numeric_columns(df)
        df = self.transformer.create_derived_columns(df)
        
        # For first record: 100 * 9.0 = 900.0
        self.assertAlmostEqual(df.iloc[0]['total_cost'], 900.0)
        # For second record: 200 * 18.0 = 3600.0
        self.assertAlmostEqual(df.iloc[1]['total_cost'], 3600.0)
    
    def test_savings_calculation(self):
        """Test savings calculation."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.convert_numeric_columns(df)
        df = self.transformer.create_derived_columns(df)
        
        # For first record: (10.0 - 9.0) * 100 = 100.0
        self.assertAlmostEqual(df.iloc[0]['savings'], 100.0)
        # For second record: (20.0 - 18.0) * 200 = 400.0
        self.assertAlmostEqual(df.iloc[1]['savings'], 400.0)
    
    def test_savings_percentage_calculation(self):
        """Test savings percentage calculation."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.convert_numeric_columns(df)
        df = self.transformer.create_derived_columns(df)
        
        # For first record: (100.0 / (10.0 * 100)) * 100 = 10.0%
        self.assertAlmostEqual(df.iloc[0]['savings_percentage'], 10.0)
        # For second record: (400.0 / (20.0 * 200)) * 100 = 10.0%
        self.assertAlmostEqual(df.iloc[1]['savings_percentage'], 10.0)
    
    def test_defect_rate_calculation(self):
        """Test defect rate calculation."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.convert_numeric_columns(df)
        df = self.transformer.create_derived_columns(df)
        
        # For first record: (5.0 / 100) * 100 = 5.0%
        self.assertAlmostEqual(df.iloc[0]['defect_rate'], 5.0)
        # For second record: (10.0 / 200) * 100 = 5.0%
        self.assertAlmostEqual(df.iloc[1]['defect_rate'], 5.0)
    
    def test_lead_time_calculation(self):
        """Test lead time calculation."""
        df = self.transformer.standardize_column_names(self.sample_data.copy())
        df = self.transformer.convert_date_columns(df)
        df = self.transformer.create_derived_columns(df)
        
        # For first record: 2023-01-10 - 2023-01-01 = 9 days
        self.assertEqual(df.iloc[0]['lead_time_days'], 9)
        # For second record: 2023-01-12 - 2023-01-02 = 10 days
        self.assertEqual(df.iloc[1]['lead_time_days'], 10)
    
    def test_missing_value_handling(self):
        """Test handling of missing values."""
        # Create data with missing values
        df_missing = pd.DataFrame({
            'PO_ID': ['PO-00001', 'PO-00002'],
            'Supplier': ['Alpha_Inc', 'Beta_Supplies'],
            'Order_Date': ['2023-01-01', '2023-01-02'],
            'Delivery_Date': ['2023-01-10', None],  # Missing delivery date
            'Item_Category': ['Office Supplies', 'Electronics'],
            'Order_Status': ['Delivered', 'Pending'],
            'Quantity': [100, 200],
            'Unit_Price': [10.0, 20.0],
            'Negotiated_Price': [9.0, 18.0],
            'Defective_Units': [5.0, None],  # Missing defective units
            'Compliance': ['Yes', 'Yes']
        })
        
        df = self.transformer.standardize_column_names(df_missing)
        df = self.transformer.convert_date_columns(df)
        df = self.transformer.convert_numeric_columns(df)
        df = self.transformer.create_derived_columns(df)
        
        # Check that missing delivery_date results in NaN lead_time_days
        self.assertTrue(pd.isna(df.iloc[1]['lead_time_days']))
        
        # Check that missing defective_units results in NaN defect_rate
        self.assertTrue(pd.isna(df.iloc[1]['defect_rate']))
    
    def test_negative_values_validation(self):
        """Test validation of negative values."""
        # Create data with negative values
        df_invalid = pd.DataFrame({
            'PO_ID': ['PO-00001', 'PO-00002'],
            'Supplier': ['Alpha_Inc', 'Beta_Supplies'],
            'Order_Date': ['2023-01-01', '2023-01-02'],
            'Delivery_Date': ['2023-01-10', '2023-01-12'],
            'Item_Category': ['Office Supplies', 'Electronics'],
            'Order_Status': ['Delivered', 'Pending'],
            'Quantity': [-100, 200],  # Negative quantity
            'Unit_Price': [10.0, -20.0],  # Negative price
            'Negotiated_Price': [9.0, 18.0],
            'Defective_Units': [5.0, 10.0],
            'Compliance': ['Yes', 'Yes']
        })
        
        df = self.transformer.standardize_column_names(df_invalid)
        df = self.transformer.convert_numeric_columns(df)
        df = self.transformer.validate_data(df)
        
        # Should detect invalid records
        self.assertGreater(len(self.transformer.transformation_stats['invalid_records']), 0)


class TestDataValidator(unittest.TestCase):
    """Test cases for DataValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        
        # Create sample data
        self.sample_df = pd.DataFrame({
            'po_id': ['PO-00001', 'PO-00002'],
            'supplier': ['Alpha_Inc', 'Beta_Supplies'],
            'order_date': pd.to_datetime(['2023-01-01', '2023-01-02']),
            'delivery_date': pd.to_datetime(['2023-01-10', '2023-01-12']),
            'item_category': ['Office Supplies', 'Electronics'],
            'order_status': ['Delivered', 'Pending'],
            'quantity': [100, 200],
            'unit_price': [10.0, 20.0],
            'negotiated_price': [9.0, 18.0],
            'defective_units': [5.0, 10.0],
            'compliance': ['Yes', 'Yes'],
            'total_cost': [900.0, 3600.0],
            'savings': [100.0, 400.0],
            'savings_percentage': [10.0, 10.0],
            'defect_rate': [5.0, 5.0],
            'lead_time_days': [9, 10],
            'order_year': [2023, 2023],
            'order_month': [1, 1],
            'order_quarter': [1, 1]
        })
        
        self.extraction_metadata = {
            'file_path': 'test.csv',
            'total_records': 2,
            'total_columns': 11,
            'columns': ['PO_ID', 'Supplier'],
            'file_size_bytes': 1024
        }
        
        self.transformation_stats = {
            'records_before': 2,
            'records_after': 2,
            'duplicates_removed': 0,
            'invalid_records': [],
            'missing_values_before': {'Delivery_Date': 0},
            'missing_values_after': {'delivery_date': 0}
        }
    
    def test_generate_validation_report(self):
        """Test validation report generation."""
        report = self.validator.generate_validation_report(
            self.sample_df,
            self.extraction_metadata,
            self.transformation_stats
        )
        
        # Check report structure
        self.assertIn('report_timestamp', report)
        self.assertIn('extraction_phase', report)
        self.assertIn('transformation_phase', report)
        self.assertIn('final_dataset', report)
        self.assertIn('data_quality', report)
        self.assertIn('business_metrics', report)
        
        # Check extraction phase
        self.assertEqual(report['extraction_phase']['total_records_extracted'], 2)
        
        # Check final dataset
        self.assertEqual(report['final_dataset']['total_records'], 2)
        
        # Check business metrics
        self.assertIn('total_cost_sum', report['business_metrics'])
        self.assertIn('total_savings', report['business_metrics'])


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
