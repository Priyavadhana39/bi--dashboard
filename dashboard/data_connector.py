"""
Data Connector Module
Fetches data from PostgreSQL database for the BI dashboard.
"""

import pandas as pd
import logging
from typing import Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class DashboardDataConnector:
    """Connects to PostgreSQL and fetches data for dashboard."""
    
    def __init__(self):
        """Initialize the data connector."""
        self.db = DatabaseConnection()
        self._cache = {}
    
    def get_purchase_orders(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Get all purchase orders with supplier and category names.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with purchase order details
        """
        if use_cache and 'purchase_orders' in self._cache:
            logger.info("Using cached purchase orders data")
            return self._cache['purchase_orders'].copy()
        
        logger.info("Fetching purchase orders from database...")
        
        query = """
        SELECT 
            po.po_id,
            s.supplier_name as supplier,
            ic.category_name as item_category,
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
        
        self._cache['purchase_orders'] = df.copy()
        logger.info(f"Fetched {len(df)} purchase orders")
        
        return df
    
    def get_supplier_performance(self) -> pd.DataFrame:
        """
        Get supplier performance metrics.
        
        Returns:
            DataFrame with supplier performance
        """
        logger.info("Fetching supplier performance from database...")
        
        query = """
        SELECT * FROM vw_supplier_performance
        ORDER BY total_cost DESC
        """
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Fetched performance for {len(df)} suppliers")
        return df
    
    def get_category_performance(self) -> pd.DataFrame:
        """
        Get category performance metrics.
        
        Returns:
            DataFrame with category performance
        """
        logger.info("Fetching category performance from database...")
        
        query = """
        SELECT * FROM vw_category_performance
        ORDER BY total_cost DESC
        """
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Fetched performance for {len(df)} categories")
        return df
    
    def get_kpi_summary(self) -> dict:
        """
        Get high-level KPI summary.
        
        Returns:
            Dictionary with KPI values
        """
        df = self.get_purchase_orders()
        
        kpis = {
            'total_cost': df['total_cost'].sum(),
            'total_savings': df['savings'].sum(),
            'total_quantity': df['quantity'].sum(),
            'total_orders': len(df),
            'avg_savings_pct': df['savings_percentage'].mean(),
            'avg_lead_time': df['lead_time_days'].mean(),
            'avg_defect_rate': df['defect_rate'].mean(),
            'orders_with_delivery_date': df['delivery_date'].notna().sum(),
            'orders_with_defect_data': df['defective_units'].notna().sum(),
            'compliant_orders': df['compliance'].sum(),
            'compliance_rate': (df['compliance'].sum() / len(df)) * 100
        }
        
        return kpis
    
    def clear_cache(self):
        """Clear the data cache."""
        self._cache = {}
        logger.info("Data cache cleared")


# Global data connector instance
_data_connector = None


def get_data_connector() -> DashboardDataConnector:
    """Get or create the global data connector instance."""
    global _data_connector
    if _data_connector is None:
        _data_connector = DashboardDataConnector()
    return _data_connector
