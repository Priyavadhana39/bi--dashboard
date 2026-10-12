"""
Data Loading Module
Loads processed procurement data from CSV into PostgreSQL database.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads procurement data into PostgreSQL database."""
    
    def __init__(self, db_connection: DatabaseConnection, csv_path: str):
        """
        Initialize DataLoader.
        
        Args:
            db_connection: DatabaseConnection instance
            csv_path: Path to the processed CSV file
        """
        self.db = db_connection
        self.csv_path = Path(csv_path)
        self.load_stats = {
            'suppliers_inserted': 0,
            'categories_inserted': 0,
            'purchase_orders_inserted': 0,
            'errors': []
        }
    
    def load_csv_data(self) -> pd.DataFrame:
        """
        Load data from CSV file.
        
        Returns:
            DataFrame with processed data
        """
        logger.info(f"Loading data from: {self.csv_path}")
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        df = pd.read_csv(self.csv_path)
        logger.info(f"Loaded {len(df)} records from CSV")
        
        return df
    
    def load_suppliers(self, df: pd.DataFrame, conn) -> Dict[str, int]:
        """
        Load unique suppliers into the suppliers table.
        
        Args:
            df: DataFrame with procurement data
            conn: Database connection
            
        Returns:
            Dictionary mapping supplier name to supplier_id
        """
        logger.info("Loading suppliers...")
        
        cursor = conn.cursor()
        supplier_map = {}
        
        # Get unique suppliers
        unique_suppliers = df['supplier'].unique()
        logger.info(f"Found {len(unique_suppliers)} unique suppliers")
        
        for supplier_name in sorted(unique_suppliers):
            try:
                # Check if supplier already exists
                cursor.execute(
                    "SELECT supplier_id FROM suppliers WHERE supplier_name = %s",
                    (supplier_name,)
                )
                result = cursor.fetchone()
                
                if result:
                    supplier_id = result[0]
                    logger.debug(f"Supplier already exists: {supplier_name} (ID: {supplier_id})")
                else:
                    # Insert new supplier
                    cursor.execute(
                        """
                        INSERT INTO suppliers (supplier_name)
                        VALUES (%s)
                        RETURNING supplier_id
                        """,
                        (supplier_name,)
                    )
                    supplier_id = cursor.fetchone()[0]
                    self.load_stats['suppliers_inserted'] += 1
                    logger.info(f"Inserted supplier: {supplier_name} (ID: {supplier_id})")
                
                supplier_map[supplier_name] = supplier_id
                
            except Exception as e:
                logger.error(f"Error loading supplier {supplier_name}: {e}")
                raise
        
        logger.info(f"Loaded {len(supplier_map)} suppliers")
        return supplier_map
    
    def load_categories(self, df: pd.DataFrame, conn) -> Dict[str, int]:
        """
        Load unique item categories into the item_categories table.
        
        Args:
            df: DataFrame with procurement data
            conn: Database connection
            
        Returns:
            Dictionary mapping category name to category_id
        """
        logger.info("Loading item categories...")
        
        cursor = conn.cursor()
        category_map = {}
        
        # Get unique categories
        unique_categories = df['item_category'].unique()
        logger.info(f"Found {len(unique_categories)} unique categories")
        
        for category_name in sorted(unique_categories):
            try:
                # Check if category already exists
                cursor.execute(
                    "SELECT category_id FROM item_categories WHERE category_name = %s",
                    (category_name,)
                )
                result = cursor.fetchone()
                
                if result:
                    category_id = result[0]
                    logger.debug(f"Category already exists: {category_name} (ID: {category_id})")
                else:
                    # Insert new category
                    cursor.execute(
                        """
                        INSERT INTO item_categories (category_name)
                        VALUES (%s)
                        RETURNING category_id
                        """,
                        (category_name,)
                    )
                    category_id = cursor.fetchone()[0]
                    self.load_stats['categories_inserted'] += 1
                    logger.info(f"Inserted category: {category_name} (ID: {category_id})")
                
                category_map[category_name] = category_id
                
            except Exception as e:
                logger.error(f"Error loading category {category_name}: {e}")
                raise
        
        logger.info(f"Loaded {len(category_map)} categories")
        return category_map
    
    def load_purchase_orders(
        self,
        df: pd.DataFrame,
        supplier_map: Dict[str, int],
        category_map: Dict[str, int],
        conn
    ) -> int:
        """
        Load purchase orders into the purchase_orders table.
        
        Args:
            df: DataFrame with procurement data
            supplier_map: Mapping of supplier names to IDs
            category_map: Mapping of category names to IDs
            conn: Database connection
            
        Returns:
            Number of purchase orders inserted
        """
        logger.info("Loading purchase orders...")
        
        cursor = conn.cursor()
        
        # Prepare data for batch insert
        purchase_order_data = []
        
        for idx, row in df.iterrows():
            try:
                # Get foreign keys
                supplier_id = supplier_map[row['supplier']]
                category_id = category_map[row['item_category']]
                
                # Convert dates (handle NaT/NaN)
                order_date = pd.to_datetime(row['order_date']).date() if pd.notna(row['order_date']) else None
                delivery_date = pd.to_datetime(row['delivery_date']).date() if pd.notna(row['delivery_date']) else None
                
                # Convert compliance to boolean
                compliance = row['compliance'].strip().lower() == 'yes'
                
                # Handle nullable numeric fields
                defective_units = float(row['defective_units']) if pd.notna(row['defective_units']) else None
                defect_rate = float(row['defect_rate']) if pd.notna(row['defect_rate']) else None
                lead_time_days = int(row['lead_time_days']) if pd.notna(row['lead_time_days']) else None
                
                # Prepare row data
                po_data = (
                    row['po_id'],
                    supplier_id,
                    category_id,
                    order_date,
                    delivery_date,
                    row['order_status'],
                    compliance,
                    int(row['quantity']),
                    float(row['unit_price']),
                    float(row['negotiated_price']),
                    defective_units,
                    float(row['total_cost']),
                    float(row['savings']),
                    float(row['savings_percentage']),
                    defect_rate,
                    lead_time_days,
                    int(row['order_year']),
                    int(row['order_month']),
                    int(row['order_quarter'])
                )
                
                purchase_order_data.append(po_data)
                
            except Exception as e:
                error_msg = f"Error preparing purchase order {row['po_id']}: {e}"
                logger.error(error_msg)
                self.load_stats['errors'].append(error_msg)
                # Continue with other records
        
        logger.info(f"Prepared {len(purchase_order_data)} purchase orders for insertion")
        
        # Batch insert purchase orders
        insert_query = """
            INSERT INTO purchase_orders (
                po_id, supplier_id, category_id, order_date, delivery_date,
                order_status, compliance, quantity, unit_price, negotiated_price,
                defective_units, total_cost, savings, savings_percentage,
                defect_rate, lead_time_days, order_year, order_month, order_quarter
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (po_id) DO NOTHING
        """
        
        try:
            execute_batch(cursor, insert_query, purchase_order_data, page_size=100)
            self.load_stats['purchase_orders_inserted'] = len(purchase_order_data)
            logger.info(f"Inserted {len(purchase_order_data)} purchase orders")
        except Exception as e:
            logger.error(f"Error batch inserting purchase orders: {e}")
            raise
        
        return len(purchase_order_data)
    
    def load_all(self) -> Dict:
        """
        Load all data from CSV into database with transaction support.
        
        Returns:
            Dictionary with loading statistics
        """
        logger.info("="*80)
        logger.info("STARTING DATA LOAD PROCESS")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        try:
            # Load CSV data
            df = self.load_csv_data()
            
            # Get database connection
            conn = self.db.get_connection()
            conn.autocommit = False  # Use transaction
            
            try:
                # Load dimension tables
                supplier_map = self.load_suppliers(df, conn)
                category_map = self.load_categories(df, conn)
                
                # Load fact table
                po_count = self.load_purchase_orders(df, supplier_map, category_map, conn)
                
                # Commit transaction
                conn.commit()
                logger.info("Transaction committed successfully")
                
            except Exception as e:
                # Rollback on error
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise
            
            finally:
                conn.close()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update statistics
            self.load_stats['duration_seconds'] = duration
            self.load_stats['csv_records'] = len(df)
            
            logger.info("="*80)
            logger.info("DATA LOAD COMPLETED")
            logger.info("="*80)
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"CSV Records: {len(df)}")
            logger.info(f"Suppliers Inserted: {self.load_stats['suppliers_inserted']}")
            logger.info(f"Categories Inserted: {self.load_stats['categories_inserted']}")
            logger.info(f"Purchase Orders Inserted: {self.load_stats['purchase_orders_inserted']}")
            
            if self.load_stats['errors']:
                logger.warning(f"Errors encountered: {len(self.load_stats['errors'])}")
            
            return self.load_stats
            
        except Exception as e:
            logger.error(f"Data load failed: {e}")
            raise


def main():
    """Main entry point for data loading."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/data_load.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Initialize database connection
        db = DatabaseConnection()
        
        # Test connection
        if not db.test_connection():
            raise RuntimeError("Database connection test failed")
        
        # Initialize data loader
        csv_path = "data/processed/procurement_cleaned.csv"
        loader = DataLoader(db, csv_path)
        
        # Load data
        stats = loader.load_all()
        
        # Print summary
        print("\n" + "="*80)
        print("DATA LOAD SUMMARY")
        print("="*80)
        print(f"✓ Suppliers inserted: {stats['suppliers_inserted']}")
        print(f"✓ Categories inserted: {stats['categories_inserted']}")
        print(f"✓ Purchase orders inserted: {stats['purchase_orders_inserted']}")
        print(f"✓ Duration: {stats['duration_seconds']:.2f} seconds")
        
        if stats['errors']:
            print(f"\n⚠ Errors: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
        else:
            print("\n✓ No errors encountered")
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Data load failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
