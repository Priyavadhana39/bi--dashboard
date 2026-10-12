"""
ML Data Loader Module
Loads procurement data from PostgreSQL for ML model training and prediction.
"""

import pandas as pd
import logging
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class MLDataLoader:
    """Loads and prepares data from PostgreSQL for ML models."""
    
    def __init__(self):
        """Initialize the data loader."""
        self.db = DatabaseConnection()
        
    def load_purchase_orders(self) -> pd.DataFrame:
        """
        Load all purchase orders with supplier and category information.
        
        Returns:
            DataFrame with complete purchase order data
        """
        logger.info("Loading purchase orders from database...")
        
        query = """
        SELECT 
            po.po_id,
            s.supplier_name as supplier,
            s.supplier_id,
            ic.category_name as item_category,
            ic.category_id,
            po.order_date,
            po.delivery_date,
            po.order_status,
            po.compliance,
            po.quantity,
            po.unit_price,
            po.negotiated_price,
            po.defective_units,
            po.total_cost,
            po.savings,
            po.savings_percentage,
            po.defect_rate,
            po.lead_time_days,
            po.order_year,
            po.order_month,
            po.order_quarter
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id
        JOIN item_categories ic ON po.category_id = ic.category_id
        ORDER BY po.order_date
        """
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convert date columns
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['delivery_date'] = pd.to_datetime(df['delivery_date'])
        
        # Convert compliance to boolean
        df['compliance'] = df['compliance'].astype(bool)
        
        logger.info(f"Loaded {len(df)} purchase orders")
        logger.info(f"Date range: {df['order_date'].min()} to {df['order_date'].max()}")
        logger.info(f"Unique suppliers: {df['supplier'].nunique()}")
        logger.info(f"Unique categories: {df['item_category'].nunique()}")
        
        return df
    
    def load_supplier_aggregates(self) -> pd.DataFrame:
        """
        Load supplier-level aggregated performance metrics.
        
        Returns:
            DataFrame with supplier performance aggregates
        """
        logger.info("Loading supplier performance aggregates...")
        
        query = """
        SELECT 
            s.supplier_id,
            s.supplier_name as supplier,
            COUNT(*) as total_orders,
            SUM(po.quantity) as total_quantity,
            SUM(po.total_cost) as total_cost,
            SUM(po.savings) as total_savings,
            AVG(po.savings_percentage) as avg_savings_percentage,
            AVG(po.lead_time_days) as avg_lead_time_days,
            AVG(po.defect_rate) as avg_defect_rate,
            SUM(CASE WHEN po.compliance THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100 as compliance_rate,
            COUNT(CASE WHEN po.delivery_date IS NOT NULL THEN 1 END) as orders_with_delivery,
            COUNT(CASE WHEN po.defective_units IS NOT NULL THEN 1 END) as orders_with_defect_data
        FROM suppliers s
        JOIN purchase_orders po ON s.supplier_id = po.supplier_id
        GROUP BY s.supplier_id, s.supplier_name
        ORDER BY s.supplier_name
        """
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Loaded aggregates for {len(df)} suppliers")
        
        return df
    
    def load_category_time_series(self) -> pd.DataFrame:
        """
        Load monthly time series data by category for demand forecasting.
        
        Returns:
            DataFrame with monthly quantity by category
        """
        logger.info("Loading category time series data...")
        
        query = """
        SELECT 
            ic.category_name as item_category,
            po.order_year,
            po.order_month,
            DATE_TRUNC('month', po.order_date) as month_date,
            COUNT(*) as order_count,
            SUM(po.quantity) as total_quantity,
            SUM(po.total_cost) as total_cost
        FROM purchase_orders po
        JOIN item_categories ic ON po.category_id = ic.category_id
        GROUP BY ic.category_name, po.order_year, po.order_month, DATE_TRUNC('month', po.order_date)
        ORDER BY ic.category_name, po.order_year, po.order_month
        """
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convert month_date to datetime
        df['month_date'] = pd.to_datetime(df['month_date'])
        
        logger.info(f"Loaded time series with {len(df)} category-month records")
        logger.info(f"Categories: {df['item_category'].nunique()}")
        logger.info(f"Date range: {df['month_date'].min()} to {df['month_date'].max()}")
        
        return df
    
    def load_overall_time_series(self) -> pd.DataFrame:
        """
        Load overall monthly time series data for demand forecasting.
        
        Returns:
            DataFrame with monthly aggregate quantity
        """
        logger.info("Loading overall time series data...")
        
        query = """
        SELECT 
            order_year,
            order_month,
            DATE_TRUNC('month', order_date) as month_date,
            COUNT(*) as order_count,
            SUM(quantity) as total_quantity,
            SUM(total_cost) as total_cost
        FROM purchase_orders
        GROUP BY order_year, order_month, DATE_TRUNC('month', order_date)
        ORDER BY order_year, order_month
        """
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convert month_date to datetime
        df['month_date'] = pd.to_datetime(df['month_date'])
        
        logger.info(f"Loaded {len(df)} monthly records")
        logger.info(f"Date range: {df['month_date'].min()} to {df['month_date'].max()}")
        
        return df
    
    def get_data_summary(self) -> dict:
        """
        Get summary statistics of the dataset.
        
        Returns:
            Dictionary with data summary
        """
        df = self.load_purchase_orders()
        
        summary = {
            'total_orders': len(df),
            'date_range_start': df['order_date'].min(),
            'date_range_end': df['order_date'].max(),
            'suppliers': df['supplier'].nunique(),
            'categories': df['item_category'].nunique(),
            'missing_delivery_date': df['delivery_date'].isna().sum(),
            'missing_defect_data': df['defective_units'].isna().sum(),
            'total_quantity': df['quantity'].sum(),
            'total_cost': df['total_cost'].sum(),
            'total_savings': df['savings'].sum(),
        }
        
        return summary


def load_ml_data():
    """
    Convenience function to load all ML data.
    
    Returns:
        Tuple of (purchase_orders, supplier_aggregates, time_series)
    """
    loader = MLDataLoader()
    
    purchase_orders = loader.load_purchase_orders()
    supplier_aggregates = loader.load_supplier_aggregates()
    time_series = loader.load_category_time_series()
    
    return purchase_orders, supplier_aggregates, time_series
