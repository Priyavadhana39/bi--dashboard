"""
Validate Module
Handles data validation and report generation.
"""

import pandas as pd
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates transformed data and generates reports."""
    
    def __init__(self):
        """Initialize the DataValidator."""
        self.validation_report = {}
    
    def generate_validation_report(
        self,
        df: pd.DataFrame,
        extraction_metadata: Dict,
        transformation_stats: Dict
    ) -> Dict:
        """
        Generate comprehensive validation report.
        
        Args:
            df: Transformed DataFrame
            extraction_metadata: Metadata from extraction phase
            transformation_stats: Statistics from transformation phase
            
        Returns:
            Dictionary containing validation report
        """
        logger.info("Generating validation report...")
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'extraction_phase': self._extract_phase_report(extraction_metadata),
            'transformation_phase': self._transformation_phase_report(transformation_stats),
            'final_dataset': self._final_dataset_report(df),
            'data_quality': self._data_quality_report(df),
            'business_metrics': self._business_metrics_report(df)
        }
        
        self.validation_report = report
        logger.info("Validation report generated successfully")
        
        return report
    
    def _extract_phase_report(self, metadata: Dict) -> Dict:
        """Generate extraction phase report."""
        return {
            'source_file': metadata['file_path'],
            'file_size_bytes': metadata['file_size_bytes'],
            'total_records_extracted': metadata['total_records'],
            'total_columns_extracted': metadata['total_columns'],
            'source_columns': metadata['columns']
        }
    
    def _transformation_phase_report(self, stats: Dict) -> Dict:
        """Generate transformation phase report."""
        return {
            'records_before_transformation': stats['records_before'],
            'records_after_transformation': stats['records_after'],
            'duplicate_records_removed': stats['duplicates_removed'],
            'invalid_records_detected': len(stats['invalid_records']),
            'invalid_record_indices': stats['invalid_records'],
            'missing_values_before': stats['missing_values_before'],
            'missing_values_after': stats['missing_values_after']
        }
    
    def _final_dataset_report(self, df: pd.DataFrame) -> Dict:
        """Generate final dataset report."""
        return {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'memory_usage_bytes': df.memory_usage(deep=True).sum()
        }
    
    def _data_quality_report(self, df: pd.DataFrame) -> Dict:
        """Generate data quality report."""
        quality_report = {}
        
        # Date range
        if 'order_date' in df.columns:
            quality_report['order_date_range'] = {
                'min': df['order_date'].min().isoformat() if pd.notna(df['order_date'].min()) else None,
                'max': df['order_date'].max().isoformat() if pd.notna(df['order_date'].max()) else None,
                'missing_count': df['order_date'].isna().sum()
            }
        
        if 'delivery_date' in df.columns:
            quality_report['delivery_date_range'] = {
                'min': df['delivery_date'].min().isoformat() if pd.notna(df['delivery_date'].min()) else None,
                'max': df['delivery_date'].max().isoformat() if pd.notna(df['delivery_date'].max()) else None,
                'missing_count': df['delivery_date'].isna().sum()
            }
        
        # Categorical value counts
        if 'supplier' in df.columns:
            quality_report['unique_suppliers'] = int(df['supplier'].nunique())
            quality_report['supplier_distribution'] = df['supplier'].value_counts().to_dict()
        
        if 'item_category' in df.columns:
            quality_report['unique_item_categories'] = int(df['item_category'].nunique())
            quality_report['item_category_distribution'] = df['item_category'].value_counts().to_dict()
        
        if 'order_status' in df.columns:
            quality_report['unique_order_statuses'] = int(df['order_status'].nunique())
            quality_report['order_status_distribution'] = df['order_status'].value_counts().to_dict()
        
        if 'compliance' in df.columns:
            quality_report['compliance_distribution'] = df['compliance'].value_counts().to_dict()
        
        return quality_report
    
    def _business_metrics_report(self, df: pd.DataFrame) -> Dict:
        """Generate business metrics report."""
        metrics = {}
        
        # Total cost metrics
        if 'total_cost' in df.columns:
            metrics['total_cost_sum'] = float(df['total_cost'].sum())
            metrics['total_cost_mean'] = float(df['total_cost'].mean())
            metrics['total_cost_median'] = float(df['total_cost'].median())
        
        # Savings metrics
        if 'savings' in df.columns:
            metrics['total_savings'] = float(df['savings'].sum())
            metrics['average_savings'] = float(df['savings'].mean())
        
        if 'savings_percentage' in df.columns:
            metrics['average_savings_percentage'] = float(df['savings_percentage'].mean())
        
        # Defect rate metrics
        if 'defect_rate' in df.columns:
            metrics['average_defect_rate'] = float(df['defect_rate'].mean())
            metrics['max_defect_rate'] = float(df['defect_rate'].max())
            metrics['records_with_defects'] = int(df['defect_rate'].notna().sum())
        
        # Lead time metrics
        if 'lead_time_days' in df.columns:
            metrics['average_lead_time_days'] = float(df['lead_time_days'].mean())
            metrics['min_lead_time_days'] = float(df['lead_time_days'].min())
            metrics['max_lead_time_days'] = float(df['lead_time_days'].max())
            metrics['records_with_lead_time'] = int(df['lead_time_days'].notna().sum())
        
        # Order metrics
        if 'quantity' in df.columns:
            metrics['total_quantity_ordered'] = int(df['quantity'].sum())
            metrics['average_order_quantity'] = float(df['quantity'].mean())
        
        return metrics
    
    def print_report_summary(self) -> None:
        """Print a formatted summary of the validation report."""
        if not self.validation_report:
            logger.warning("No validation report available")
            return
        
        report = self.validation_report
        
        print("\n" + "="*80)
        print("ETL VALIDATION REPORT")
        print("="*80)
        
        # Extraction Phase
        print("\n--- EXTRACTION PHASE ---")
        extraction = report['extraction_phase']
        print(f"Source File: {extraction['source_file']}")
        print(f"Total Records Extracted: {extraction['total_records_extracted']}")
        print(f"Total Columns Extracted: {extraction['total_columns_extracted']}")
        print(f"File Size: {extraction['file_size_bytes']:,} bytes")
        
        # Transformation Phase
        print("\n--- TRANSFORMATION PHASE ---")
        transformation = report['transformation_phase']
        print(f"Records Before: {transformation['records_before_transformation']}")
        print(f"Records After: {transformation['records_after_transformation']}")
        print(f"Duplicate Records Removed: {transformation['duplicate_records_removed']}")
        print(f"Invalid Records Detected: {transformation['invalid_records_detected']}")
        
        # Missing values
        print("\nMissing Values Before Transformation:")
        for col, count in transformation['missing_values_before'].items():
            if count > 0:
                print(f"  {col}: {count}")
        
        print("\nMissing Values After Transformation:")
        for col, count in transformation['missing_values_after'].items():
            if count > 0:
                print(f"  {col}: {count}")
        
        # Final Dataset
        print("\n--- FINAL DATASET ---")
        final = report['final_dataset']
        print(f"Total Records: {final['total_records']}")
        print(f"Total Columns: {final['total_columns']}")
        print(f"Columns: {', '.join(final['columns'])}")
        
        # Data Quality
        print("\n--- DATA QUALITY ---")
        quality = report['data_quality']
        
        if 'order_date_range' in quality:
            date_range = quality['order_date_range']
            print(f"Order Date Range: {date_range['min']} to {date_range['max']}")
            print(f"Missing Order Dates: {date_range['missing_count']}")
        
        if 'delivery_date_range' in quality:
            delivery_range = quality['delivery_date_range']
            print(f"Delivery Date Missing: {delivery_range['missing_count']}")
        
        if 'unique_suppliers' in quality:
            print(f"Number of Suppliers: {quality['unique_suppliers']}")
        
        if 'unique_item_categories' in quality:
            print(f"Number of Item Categories: {quality['unique_item_categories']}")
        
        if 'unique_order_statuses' in quality:
            print(f"Number of Order Statuses: {quality['unique_order_statuses']}")
        
        # Business Metrics
        print("\n--- BUSINESS METRICS ---")
        metrics = report['business_metrics']
        
        if 'total_cost_sum' in metrics:
            print(f"Total Cost Sum: ${metrics['total_cost_sum']:,.2f}")
        
        if 'total_savings' in metrics:
            print(f"Total Savings: ${metrics['total_savings']:,.2f}")
        
        if 'average_savings_percentage' in metrics:
            print(f"Average Savings Percentage: {metrics['average_savings_percentage']:.2f}%")
        
        if 'average_defect_rate' in metrics:
            print(f"Average Defect Rate: {metrics['average_defect_rate']:.2f}%")
            print(f"Records with Defects: {metrics['records_with_defects']}")
        
        if 'average_lead_time_days' in metrics:
            print(f"Average Lead Time: {metrics['average_lead_time_days']:.2f} days")
            print(f"Records with Lead Time: {metrics['records_with_lead_time']}")
        
        print("\n" + "="*80)
    
    def save_report_to_file(self, output_path: str) -> None:
        """
        Save validation report to JSON file.
        
        Args:
            output_path: Path to save the report
        """
        import json
        
        if not self.validation_report:
            logger.warning("No validation report available to save")
            return
        
        try:
            with open(output_path, 'w') as f:
                json.dump(self.validation_report, f, indent=2, default=str)
            logger.info(f"Validation report saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving validation report: {e}")
            raise
