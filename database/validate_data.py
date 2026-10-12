"""
Database Validation Module
Validates loaded data by comparing CSV and PostgreSQL database totals.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime
import psycopg2

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data integrity between CSV and PostgreSQL."""
    
    def __init__(self, db_connection: DatabaseConnection, csv_path: str):
        """
        Initialize DataValidator.
        
        Args:
            db_connection: DatabaseConnection instance
            csv_path: Path to the processed CSV file
        """
        self.db = db_connection
        self.csv_path = Path(csv_path)
        self.validation_results = {
            'csv_metrics': {},
            'db_metrics': {},
            'comparisons': {},
            'passed': [],
            'failed': []
        }
    
    def load_csv_metrics(self) -> Dict:
        """
        Calculate metrics from CSV file.
        
        Returns:
            Dictionary with CSV metrics
        """
        logger.info("Calculating CSV metrics...")
        
        df = pd.read_csv(self.csv_path)
        
        metrics = {
            'total_records': len(df),
            'unique_po_ids': df['po_id'].nunique(),
            'unique_suppliers': df['supplier'].nunique(),
            'unique_categories': df['item_category'].nunique(),
            'total_quantity': int(df['quantity'].sum()),
            'total_cost': float(df['total_cost'].sum()),
            'total_savings': float(df['savings'].sum()),
            'avg_savings_percentage': float(df['savings_percentage'].mean()),
            'avg_defect_rate': float(df['defect_rate'].mean()),
            'avg_lead_time': float(df['lead_time_days'].mean()),
            'missing_delivery_dates': int(df['delivery_date'].isna().sum()),
            'missing_defective_units': int(df['defective_units'].isna().sum()),
            'order_status_counts': df['order_status'].value_counts().to_dict(),
            'compliance_counts': df['compliance'].value_counts().to_dict()
        }
        
        self.validation_results['csv_metrics'] = metrics
        logger.info(f"CSV metrics calculated: {len(df)} records")
        
        return metrics
    
    def load_db_metrics(self) -> Dict:
        """
        Calculate metrics from PostgreSQL database.
        
        Returns:
            Dictionary with database metrics
        """
        logger.info("Calculating database metrics...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        metrics = {}
        
        try:
            # Total records in each table
            cursor.execute("SELECT COUNT(*) FROM suppliers")
            metrics['supplier_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM item_categories")
            metrics['category_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM purchase_orders")
            metrics['total_records'] = cursor.fetchone()[0]
            
            # Unique PO IDs (should match total_records)
            cursor.execute("SELECT COUNT(DISTINCT po_id) FROM purchase_orders")
            metrics['unique_po_ids'] = cursor.fetchone()[0]
            
            # Unique suppliers and categories
            cursor.execute("SELECT COUNT(DISTINCT supplier_id) FROM purchase_orders")
            metrics['unique_suppliers'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT category_id) FROM purchase_orders")
            metrics['unique_categories'] = cursor.fetchone()[0]
            
            # Total quantity
            cursor.execute("SELECT SUM(quantity) FROM purchase_orders")
            metrics['total_quantity'] = int(cursor.fetchone()[0] or 0)
            
            # Total cost
            cursor.execute("SELECT SUM(total_cost) FROM purchase_orders")
            metrics['total_cost'] = float(cursor.fetchone()[0] or 0)
            
            # Total savings
            cursor.execute("SELECT SUM(savings) FROM purchase_orders")
            metrics['total_savings'] = float(cursor.fetchone()[0] or 0)
            
            # Average savings percentage
            cursor.execute("SELECT AVG(savings_percentage) FROM purchase_orders")
            metrics['avg_savings_percentage'] = float(cursor.fetchone()[0] or 0)
            
            # Average defect rate (excluding NULLs)
            cursor.execute("SELECT AVG(defect_rate) FROM purchase_orders WHERE defect_rate IS NOT NULL")
            result = cursor.fetchone()[0]
            metrics['avg_defect_rate'] = float(result) if result else 0
            
            # Average lead time (excluding NULLs)
            cursor.execute("SELECT AVG(lead_time_days) FROM purchase_orders WHERE lead_time_days IS NOT NULL")
            result = cursor.fetchone()[0]
            metrics['avg_lead_time'] = float(result) if result else 0
            
            # Missing values
            cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE delivery_date IS NULL")
            metrics['missing_delivery_dates'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE defective_units IS NULL")
            metrics['missing_defective_units'] = cursor.fetchone()[0]
            
            # Order status counts
            cursor.execute("SELECT order_status, COUNT(*) FROM purchase_orders GROUP BY order_status")
            metrics['order_status_counts'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Compliance counts
            cursor.execute("SELECT compliance, COUNT(*) FROM purchase_orders GROUP BY compliance")
            compliance_results = cursor.fetchall()
            metrics['compliance_counts'] = {
                'Yes' if row[0] else 'No': row[1] for row in compliance_results
            }
            
            self.validation_results['db_metrics'] = metrics
            logger.info(f"Database metrics calculated: {metrics['total_records']} records")
            
        except Exception as e:
            logger.error(f"Error calculating database metrics: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        return metrics
    
    def check_referential_integrity(self) -> Dict:
        """
        Check referential integrity constraints.
        
        Returns:
            Dictionary with integrity check results
        """
        logger.info("Checking referential integrity...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        integrity_checks = {}
        
        try:
            # Check for orphaned records (should be 0)
            cursor.execute("""
                SELECT COUNT(*)
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
                WHERE s.supplier_id IS NULL
            """)
            integrity_checks['orphaned_supplier_refs'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM purchase_orders po
                LEFT JOIN item_categories ic ON po.category_id = ic.category_id
                WHERE ic.category_id IS NULL
            """)
            integrity_checks['orphaned_category_refs'] = cursor.fetchone()[0]
            
            # Check for duplicate PO IDs (should be 0)
            cursor.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT po_id, COUNT(*) as cnt
                    FROM purchase_orders
                    GROUP BY po_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
            integrity_checks['duplicate_po_ids'] = cursor.fetchone()[0]
            
            logger.info("Referential integrity checks completed")
            
        except Exception as e:
            logger.error(f"Error checking referential integrity: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        return integrity_checks
    
    def compare_metrics(self) -> None:
        """Compare CSV and database metrics."""
        logger.info("Comparing CSV and database metrics...")
        
        csv = self.validation_results['csv_metrics']
        db = self.validation_results['db_metrics']
        
        comparisons = []
        
        # Define metrics to compare with tolerance
        metrics_to_compare = [
            ('total_records', 0),
            ('unique_po_ids', 0),
            ('unique_suppliers', 0),
            ('unique_categories', 0),
            ('total_quantity', 0),
            ('total_cost', 0.01),  # Allow small floating point differences
            ('total_savings', 0.01),
            ('avg_savings_percentage', 0.01),
            ('missing_delivery_dates', 0),
            ('missing_defective_units', 0)
        ]
        
        for metric_name, tolerance in metrics_to_compare:
            csv_value = csv.get(metric_name, 0)
            db_value = db.get(metric_name, 0)
            
            # Compare with tolerance
            if isinstance(csv_value, (int, float)) and isinstance(db_value, (int, float)):
                diff = abs(csv_value - db_value)
                match = diff <= tolerance
            else:
                match = csv_value == db_value
            
            comparison = {
                'metric': metric_name,
                'csv_value': csv_value,
                'db_value': db_value,
                'match': match,
                'difference': csv_value - db_value if isinstance(csv_value, (int, float)) else 'N/A'
            }
            
            comparisons.append(comparison)
            
            if match:
                self.validation_results['passed'].append(metric_name)
                logger.info(f"✓ {metric_name}: MATCH")
            else:
                self.validation_results['failed'].append(metric_name)
                logger.warning(f"✗ {metric_name}: MISMATCH (CSV: {csv_value}, DB: {db_value})")
        
        self.validation_results['comparisons'] = comparisons
    
    def validate_all(self) -> Dict:
        """
        Run complete validation process.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("="*80)
        logger.info("STARTING DATABASE VALIDATION")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        try:
            # Load metrics
            self.load_csv_metrics()
            self.load_db_metrics()
            
            # Compare metrics
            self.compare_metrics()
            
            # Check referential integrity
            integrity = self.check_referential_integrity()
            self.validation_results['referential_integrity'] = integrity
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.validation_results['validation_time'] = duration
            self.validation_results['timestamp'] = datetime.now().isoformat()
            
            # Determine overall validation status
            all_passed = (
                len(self.validation_results['failed']) == 0 and
                integrity['orphaned_supplier_refs'] == 0 and
                integrity['orphaned_category_refs'] == 0 and
                integrity['duplicate_po_ids'] == 0
            )
            
            self.validation_results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
            
            logger.info("="*80)
            logger.info(f"VALIDATION {self.validation_results['overall_status']}")
            logger.info("="*80)
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Passed: {len(self.validation_results['passed'])}")
            logger.info(f"Failed: {len(self.validation_results['failed'])}")
            
            return self.validation_results
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
    
    def print_validation_report(self) -> None:
        """Print detailed validation report."""
        results = self.validation_results
        
        print("\n" + "="*80)
        print("DATABASE VALIDATION REPORT")
        print("="*80)
        
        # Summary
        print(f"\nValidation Status: {results.get('overall_status', 'UNKNOWN')}")
        print(f"Validation Time: {results.get('validation_time', 0):.2f} seconds")
        print(f"Timestamp: {results.get('timestamp', 'N/A')}")
        
        # CSV Metrics
        print("\n--- CSV METRICS ---")
        csv = results.get('csv_metrics', {})
        print(f"Total Records: {csv.get('total_records', 0)}")
        print(f"Unique Suppliers: {csv.get('unique_suppliers', 0)}")
        print(f"Unique Categories: {csv.get('unique_categories', 0)}")
        print(f"Total Quantity: {csv.get('total_quantity', 0):,}")
        print(f"Total Cost: ${csv.get('total_cost', 0):,.2f}")
        print(f"Total Savings: ${csv.get('total_savings', 0):,.2f}")
        
        # Database Metrics
        print("\n--- DATABASE METRICS ---")
        db = results.get('db_metrics', {})
        print(f"Suppliers in DB: {db.get('supplier_count', 0)}")
        print(f"Categories in DB: {db.get('category_count', 0)}")
        print(f"Purchase Orders in DB: {db.get('total_records', 0)}")
        print(f"Total Quantity: {db.get('total_quantity', 0):,}")
        print(f"Total Cost: ${db.get('total_cost', 0):,.2f}")
        print(f"Total Savings: ${db.get('total_savings', 0):,.2f}")
        
        # Comparisons
        print("\n--- METRIC COMPARISONS ---")
        for comp in results.get('comparisons', []):
            status = "✓" if comp['match'] else "✗"
            metric = comp['metric'].replace('_', ' ').title()
            print(f"{status} {metric}: CSV={comp['csv_value']}, DB={comp['db_value']}")
        
        # Referential Integrity
        print("\n--- REFERENTIAL INTEGRITY ---")
        integrity = results.get('referential_integrity', {})
        print(f"✓ Orphaned Supplier References: {integrity.get('orphaned_supplier_refs', 0)}")
        print(f"✓ Orphaned Category References: {integrity.get('orphaned_category_refs', 0)}")
        print(f"✓ Duplicate PO IDs: {integrity.get('duplicate_po_ids', 0)}")
        
        # Summary
        print("\n--- VALIDATION SUMMARY ---")
        print(f"Tests Passed: {len(results.get('passed', []))}")
        print(f"Tests Failed: {len(results.get('failed', []))}")
        
        if results.get('failed'):
            print("\nFailed Tests:")
            for failed in results['failed']:
                print(f"  - {failed}")
        
        print("\n" + "="*80)
    
    def save_validation_report(self, output_path: str) -> None:
        """
        Save validation report to JSON file.
        
        Args:
            output_path: Path to save the report
        """
        import json
        
        try:
            with open(output_path, 'w') as f:
                json.dump(self.validation_results, f, indent=2, default=str)
            logger.info(f"Validation report saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving validation report: {e}")
            raise


def main():
    """Main entry point for database validation."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/data_validation.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Initialize database connection
        db = DatabaseConnection()
        
        # Test connection
        if not db.test_connection():
            raise RuntimeError("Database connection test failed")
        
        # Initialize validator
        csv_path = "data/processed/procurement_cleaned.csv"
        validator = DataValidator(db, csv_path)
        
        # Run validation
        results = validator.validate_all()
        
        # Print report
        validator.print_validation_report()
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"logs/validation_report_db_{timestamp}.json"
        validator.save_validation_report(report_path)
        
        # Exit with appropriate code
        if results['overall_status'] == 'PASSED':
            print("\n✓ All validation checks passed")
            exit(0)
        else:
            print("\n✗ Some validation checks failed")
            exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
