"""
Database Tools for AI Agent
Read-only tools to query procurement data safely.
Uses parameterized SQL to prevent SQL injection.
"""

import psycopg2
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from agent.config import config

logger = logging.getLogger(__name__)


class DatabaseTools:
    """Read-only database access for the AI agent"""
    
    def __init__(self):
        self.connection_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }
    
    def _get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            # Set to read-only mode for safety
            conn.set_session(readonly=True, autocommit=True)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a parameterized query and return results as dict list"""
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []
            
            # Fetch results
            rows = cur.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                result = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert datetime to string for JSON serialization
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    result[col] = value
                results.append(result)
            
            cur.close()
            return results
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    # ========================================================================
    # SUPPLIER INFORMATION TOOLS
    # ========================================================================
    
    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Get list of all suppliers with basic information"""
        query = """
            SELECT 
                s.supplier_id,
                s.supplier_name as supplier,
                COUNT(DISTINCT po.po_id) as total_orders,
                SUM(po.total_cost) as total_spend,
                AVG(po.savings_percentage) as avg_savings_pct
            FROM suppliers s
            LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id
            GROUP BY s.supplier_id, s.supplier_name
            ORDER BY total_spend DESC NULLS LAST
        """
        return self._execute_query(query)
    
    def get_supplier_info(self, supplier_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific supplier"""
        query = """
            SELECT 
                s.supplier_id,
                s.supplier_name as supplier,
                COUNT(DISTINCT po.po_id) as total_orders,
                SUM(po.quantity) as total_quantity,
                SUM(po.total_cost) as total_spend,
                SUM(po.savings) as total_savings,
                AVG(po.savings_percentage) as avg_savings_pct,
                AVG(po.lead_time_days) as avg_lead_time,
                AVG(po.defect_rate) as avg_defect_rate,
                SUM(CASE WHEN po.compliance = TRUE THEN 1 ELSE 0 END)::float / 
                    NULLIF(COUNT(*), 0) * 100 as compliance_rate
            FROM suppliers s
            LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id
            WHERE LOWER(s.supplier_name) = LOWER(%s)
            GROUP BY s.supplier_id, s.supplier_name
        """
        results = self._execute_query(query, (supplier_name,))
        return results[0] if results else None
    
    def get_supplier_performance_metrics(self, supplier_name: str) -> Dict[str, Any]:
        """Get detailed performance metrics for a supplier"""
        query = """
            SELECT 
                pod.supplier_name as supplier,
                COUNT(*) as total_orders,
                AVG(CASE WHEN pod.lead_time_days IS NOT NULL THEN pod.lead_time_days END) as avg_lead_time,
                AVG(CASE WHEN pod.defect_rate IS NOT NULL THEN pod.defect_rate END) as avg_defect_rate,
                MIN(CASE WHEN pod.defect_rate IS NOT NULL THEN pod.defect_rate END) as min_defect_rate,
                MAX(CASE WHEN pod.defect_rate IS NOT NULL THEN pod.defect_rate END) as max_defect_rate,
                SUM(CASE WHEN pod.compliance = TRUE THEN 1 ELSE 0 END) as compliant_orders,
                COUNT(*) - COUNT(pod.lead_time_days) as missing_delivery_data,
                COUNT(*) - COUNT(pod.defect_rate) as missing_defect_data
            FROM vw_purchase_orders_detail pod
            WHERE LOWER(pod.supplier_name) = LOWER(%s)
            GROUP BY pod.supplier_name
        """
        results = self._execute_query(query, (supplier_name,))
        return results[0] if results else {}
    
    # ========================================================================
    # PURCHASE ORDER TOOLS
    # ========================================================================
    
    def get_supplier_orders(self, supplier_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent purchase orders for a supplier"""
        query = """
            SELECT 
                pod.po_id,
                pod.order_date,
                pod.category_name as item_category,
                pod.quantity,
                pod.unit_price,
                pod.negotiated_price,
                pod.total_cost,
                pod.savings_percentage,
                pod.lead_time_days,
                pod.defect_rate,
                pod.compliance
            FROM vw_purchase_orders_detail pod
            WHERE LOWER(pod.supplier_name) = LOWER(%s)
            ORDER BY pod.order_date DESC
            LIMIT %s
        """
        return self._execute_query(query, (supplier_name, limit))
    
    def get_order_details(self, po_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific purchase order"""
        query = """
            SELECT 
                pod.po_id,
                pod.supplier_name as supplier,
                pod.category_name as item_category,
                pod.order_date,
                pod.delivery_date,
                pod.order_status,
                pod.quantity,
                pod.unit_price,
                pod.negotiated_price,
                pod.total_cost,
                pod.savings,
                pod.savings_percentage,
                pod.lead_time_days,
                pod.defect_rate,
                pod.compliance
            FROM vw_purchase_orders_detail pod
            WHERE pod.po_id = %s
        """
        results = self._execute_query(query, (po_id,))
        return results[0] if results else None
    
    def get_recent_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent purchase orders across all suppliers"""
        query = """
            SELECT 
                pod.po_id,
                pod.supplier_name as supplier,
                pod.category_name as item_category,
                pod.order_date,
                pod.quantity,
                pod.negotiated_price,
                pod.total_cost,
                pod.order_status
            FROM vw_purchase_orders_detail pod
            ORDER BY pod.order_date DESC
            LIMIT %s
        """
        return self._execute_query(query, (limit,))
    
    # ========================================================================
    # CATEGORY TOOLS
    # ========================================================================
    
    def get_category_info(self, category: str) -> Dict[str, Any]:
        """Get information about a specific item category"""
        query = """
            SELECT 
                c.category_name as item_category,
                COUNT(po.po_id) as total_orders,
                SUM(po.quantity) as total_quantity,
                SUM(po.total_cost) as total_spend,
                AVG(po.unit_price) as avg_unit_price,
                AVG(po.negotiated_price) as avg_negotiated_price,
                AVG(po.savings_percentage) as avg_savings_pct,
                COUNT(DISTINCT po.supplier_id) as supplier_count
            FROM item_categories c
            LEFT JOIN purchase_orders po ON c.category_id = po.category_id
            WHERE LOWER(c.category_name) = LOWER(%s)
            GROUP BY c.category_name
        """
        results = self._execute_query(query, (category,))
        return results[0] if results else {}
    
    def get_category_suppliers(self, category: str) -> List[Dict[str, Any]]:
        """Get suppliers for a specific category with their performance"""
        query = """
            SELECT 
                pod.supplier_name as supplier,
                COUNT(*) as order_count,
                SUM(pod.total_cost) as total_spend,
                AVG(pod.negotiated_price) as avg_price,
                AVG(pod.savings_percentage) as avg_savings_pct,
                AVG(pod.lead_time_days) as avg_lead_time,
                AVG(pod.defect_rate) as avg_defect_rate
            FROM vw_purchase_orders_detail pod
            WHERE LOWER(pod.category_name) = LOWER(%s)
            GROUP BY pod.supplier_name
            ORDER BY total_spend DESC
        """
        return self._execute_query(query, (category,))
    
    # ========================================================================
    # SPENDING ANALYSIS TOOLS
    # ========================================================================
    
    def get_spending_by_period(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get spending aggregated by month"""
        query = """
            SELECT 
                DATE_TRUNC('month', order_date) as month,
                COUNT(*) as order_count,
                SUM(quantity) as total_quantity,
                SUM(total_cost) as total_spend,
                AVG(negotiated_price) as avg_price
            FROM purchase_orders
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND order_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND order_date <= %s"
            params.append(end_date)
        
        query += """
            GROUP BY DATE_TRUNC('month', order_date)
            ORDER BY month
        """
        
        return self._execute_query(query, tuple(params) if params else None)
    
    def get_spending_by_supplier(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get spending breakdown by supplier"""
        query = """
            SELECT 
                pod.supplier_name as supplier,
                COUNT(*) as order_count,
                SUM(pod.total_cost) as total_spend,
                AVG(pod.total_cost) as avg_order_value,
                SUM(pod.savings) as total_savings
            FROM vw_purchase_orders_detail pod
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND pod.order_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND pod.order_date <= %s"
            params.append(end_date)
        
        query += """
            GROUP BY pod.supplier_name
            ORDER BY total_spend DESC
        """
        
        return self._execute_query(query, tuple(params) if params else None)
    
    def get_spending_by_category(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get spending breakdown by category"""
        query = """
            SELECT 
                pod.category_name as item_category,
                COUNT(*) as order_count,
                SUM(pod.quantity) as total_quantity,
                SUM(pod.total_cost) as total_spend,
                AVG(pod.negotiated_price) as avg_price
            FROM vw_purchase_orders_detail pod
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND pod.order_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND pod.order_date <= %s"
            params.append(end_date)
        
        query += """
            GROUP BY pod.category_name
            ORDER BY total_spend DESC
        """
        
        return self._execute_query(query, tuple(params) if params else None)
    
    # ========================================================================
    # PRICE ANALYSIS TOOLS
    # ========================================================================
    
    def get_price_history(self, category: str = None, supplier: str = None) -> List[Dict[str, Any]]:
        """Get price history for a category and/or supplier"""
        query = """
            SELECT 
                pod.order_date,
                pod.supplier_name as supplier,
                pod.category_name as item_category,
                AVG(pod.unit_price) as avg_unit_price,
                AVG(pod.negotiated_price) as avg_negotiated_price,
                AVG(pod.savings_percentage) as avg_savings_pct
            FROM vw_purchase_orders_detail pod
            WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND LOWER(pod.category_name) = LOWER(%s)"
            params.append(category)
        
        if supplier:
            query += " AND LOWER(pod.supplier_name) = LOWER(%s)"
            params.append(supplier)
        
        query += """
            GROUP BY pod.order_date, pod.supplier_name, pod.category_name
            ORDER BY pod.order_date DESC
            LIMIT 100
        """
        
        return self._execute_query(query, tuple(params) if params else None)
    
    # ========================================================================
    # DELIVERY & QUALITY TOOLS
    # ========================================================================
    
    def get_delivery_performance(self, supplier_name: str = None) -> List[Dict[str, Any]]:
        """Get delivery performance metrics"""
        query = """
            SELECT 
                pod.supplier_name as supplier,
                COUNT(*) as total_orders,
                AVG(pod.lead_time_days) as avg_lead_time,
                COUNT(pod.lead_time_days) as orders_with_delivery_data,
                COUNT(*) - COUNT(pod.lead_time_days) as missing_data
            FROM vw_purchase_orders_detail pod
            WHERE 1=1
        """
        params = []
        
        if supplier_name:
            query += " AND LOWER(pod.supplier_name) = LOWER(%s)"
            params.append(supplier_name)
        
        query += """
            GROUP BY pod.supplier_name
            ORDER BY total_orders DESC
        """
        
        return self._execute_query(query, tuple(params) if params else None)
    
    def get_quality_metrics(self, supplier_name: str = None) -> List[Dict[str, Any]]:
        """Get quality/defect metrics"""
        query = """
            SELECT 
                pod.supplier_name as supplier,
                COUNT(*) as total_orders,
                AVG(pod.defect_rate) as avg_defect_rate,
                MIN(pod.defect_rate) as min_defect_rate,
                MAX(pod.defect_rate) as max_defect_rate,
                COUNT(pod.defect_rate) as orders_with_data,
                COUNT(*) - COUNT(pod.defect_rate) as missing_data
            FROM vw_purchase_orders_detail pod
            WHERE 1=1
        """
        params = []
        
        if supplier_name:
            query += " AND LOWER(pod.supplier_name) = LOWER(%s)"
            params.append(supplier_name)
        
        query += """
            GROUP BY pod.supplier_name
            ORDER BY avg_defect_rate
        """
        
        return self._execute_query(query, tuple(params) if params else None)
    
    # ========================================================================
    # COMPLIANCE TOOLS
    # ========================================================================
    
    def get_compliance_info(self, supplier_name: str = None) -> List[Dict[str, Any]]:
        """Get compliance information"""
        query = """
            SELECT 
                pod.supplier_name as supplier,
                COUNT(*) as total_orders,
                SUM(CASE WHEN pod.compliance = TRUE THEN 1 ELSE 0 END) as compliant_orders,
                SUM(CASE WHEN pod.compliance = FALSE THEN 1 ELSE 0 END) as non_compliant_orders,
                ROUND(SUM(CASE WHEN pod.compliance = TRUE THEN 1 ELSE 0 END)::numeric / 
                      NULLIF(COUNT(*), 0) * 100, 2) as compliance_rate
            FROM vw_purchase_orders_detail pod
            WHERE 1=1
        """
        params = []
        
        if supplier_name:
            query += " AND LOWER(pod.supplier_name) = LOWER(%s)"
            params.append(supplier_name)
        
        query += """
            GROUP BY pod.supplier_name
            ORDER BY compliance_rate DESC
        """
        
        return self._execute_query(query, tuple(params) if params else None)


# Singleton instance
db_tools = DatabaseTools()
