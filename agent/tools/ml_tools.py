"""
ML Tools for AI Agent
Tools to access Module 4 ML outputs (supplier scores, anomalies, forecasts).
Reads from existing ML tables without recalculating.
"""

import psycopg2
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from agent.config import config

logger = logging.getLogger(__name__)


class MLTools:
    """ML insights access for the AI agent"""
    
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
            
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            
            results = []
            for row in rows:
                result = {}
                for i, col in enumerate(columns):
                    value = row[i]
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
    # SUPPLIER SCORING TOOLS
    # ========================================================================
    
    def get_supplier_scores(self) -> List[Dict[str, Any]]:
        """
        Get all supplier performance scores from Module 4.
        Returns the latest scoring results.
        """
        query = """
            SELECT 
                supplier_name as supplier,
                supplier_score,
                supplier_rank,
                performance_category,
                avg_savings_percentage,
                avg_lead_time_days,
                avg_defect_rate,
                compliance_rate,
                data_completeness_pct,
                scoring_date as created_at
            FROM vw_latest_supplier_scores
            ORDER BY supplier_rank
        """
        try:
            return self._execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get supplier scores: {e}")
            return []
    
    def get_supplier_score(self, supplier_name: str) -> Optional[Dict[str, Any]]:
        """
        Get performance score for a specific supplier.
        
        Args:
            supplier_name: Name of the supplier
            
        Returns:
            Dict with score, rank, category, and metrics
        """
        query = """
            SELECT 
                supplier_name as supplier,
                supplier_score,
                supplier_rank,
                performance_category,
                avg_savings_percentage,
                avg_lead_time_days,
                avg_defect_rate,
                compliance_rate,
                data_completeness_pct,
                created_at
            FROM vw_latest_supplier_scores
            WHERE LOWER(supplier_name) = LOWER(%s)
        """
        try:
            results = self._execute_query(query, (supplier_name,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get supplier score for {supplier_name}: {e}")
            return None
    
    def get_top_suppliers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top-ranked suppliers by performance score.
        
        Args:
            limit: Number of top suppliers to return
            
        Returns:
            List of top suppliers with scores
        """
        query = """
            SELECT 
                supplier_name as supplier,
                supplier_score,
                supplier_rank,
                performance_category,
                avg_savings_percentage,
                compliance_rate
            FROM vw_latest_supplier_scores
            ORDER BY supplier_rank
            LIMIT %s
        """
        try:
            return self._execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Failed to get top suppliers: {e}")
            return []
    
    def get_poor_performing_suppliers(self, score_threshold: float = 50.0) -> List[Dict[str, Any]]:
        """
        Get suppliers with poor performance scores.
        
        Args:
            score_threshold: Suppliers below this score are considered poor
            
        Returns:
            List of poor-performing suppliers
        """
        query = """
            SELECT 
                supplier_name as supplier,
                supplier_score,
                supplier_rank,
                performance_category,
                avg_savings_percentage,
                avg_lead_time_days,
                avg_defect_rate,
                compliance_rate
            FROM vw_latest_supplier_scores
            WHERE supplier_score < %s
            ORDER BY supplier_score ASC
        """
        try:
            return self._execute_query(query, (score_threshold,))
        except Exception as e:
            logger.error(f"Failed to get poor performing suppliers: {e}")
            return []
    
    # ========================================================================
    # PRICE ANOMALY TOOLS
    # ========================================================================
    
    def get_price_anomalies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all detected price anomalies from Module 4.
        
        Args:
            limit: Maximum number of anomalies to return
            
        Returns:
            List of anomaly records
        """
        query = """
            SELECT 
                po_id,
                supplier_name as supplier,
                category_name as item_category,
                order_date,
                quantity,
                negotiated_price,
                total_cost,
                anomaly_score,
                anomaly_status,
                price_level,
                detection_date
            FROM vw_active_anomalies
            ORDER BY ABS(anomaly_score) DESC
            LIMIT %s
        """
        try:
            return self._execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Failed to get price anomalies: {e}")
            return []
    
    def get_supplier_anomalies(self, supplier_name: str) -> List[Dict[str, Any]]:
        """
        Get price anomalies for a specific supplier.
        
        Args:
            supplier_name: Name of the supplier
            
        Returns:
            List of anomalies for the supplier
        """
        query = """
            SELECT 
                po_id,
                supplier_name as supplier,
                category_name as item_category,
                order_date,
                quantity,
                negotiated_price,
                total_cost,
                anomaly_score,
                anomaly_status,
                price_level
            FROM vw_active_anomalies
            WHERE LOWER(supplier_name) = LOWER(%s)
            ORDER BY ABS(anomaly_score) DESC
        """
        try:
            return self._execute_query(query, (supplier_name,))
        except Exception as e:
            logger.error(f"Failed to get anomalies for {supplier_name}: {e}")
            return []
    
    def get_category_anomalies(self, category: str) -> List[Dict[str, Any]]:
        """
        Get price anomalies for a specific category.
        
        Args:
            category: Item category name
            
        Returns:
            List of anomalies for the category
        """
        query = """
            SELECT 
                po_id,
                supplier_name as supplier,
                category_name as item_category,
                order_date,
                unit_price,
                negotiated_price,
                anomaly_score,
                anomaly_status,
                price_level
            FROM vw_active_anomalies
            WHERE LOWER(item_category) = LOWER(%s)
            ORDER BY ABS(anomaly_score) DESC
        """
        try:
            return self._execute_query(query, (category,))
        except Exception as e:
            logger.error(f"Failed to get anomalies for {category}: {e}")
            return []
    
    def get_high_severity_anomalies(self, severity_threshold: float = -0.6) -> List[Dict[str, Any]]:
        """
        Get high-severity price anomalies.
        
        Args:
            severity_threshold: Anomalies with scores below this are high severity
            
        Returns:
            List of high-severity anomalies
        """
        query = """
            SELECT 
                po_id,
                supplier_name as supplier,
                category_name as item_category,
                order_date,
                negotiated_price,
                anomaly_score,
                price_level
            FROM vw_active_anomalies
            WHERE anomaly_score < %s
            ORDER BY anomaly_score ASC
            LIMIT 20
        """
        try:
            return self._execute_query(query, (severity_threshold,))
        except Exception as e:
            logger.error(f"Failed to get high severity anomalies: {e}")
            return []
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about price anomalies.
        
        Returns:
            Summary with total anomalies, by price level, by supplier
        """
        query = """
            SELECT 
                COUNT(*) as total_anomalies,
                COUNT(CASE WHEN price_level = 'High' THEN 1 END) as high_price_count,
                COUNT(CASE WHEN price_level = 'Low' THEN 1 END) as low_price_count,
                AVG(anomaly_score) as avg_anomaly_score,
                MIN(anomaly_score) as most_severe_score
            FROM vw_active_anomalies
        """
        try:
            results = self._execute_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Failed to get anomaly summary: {e}")
            return {}
    
    # ========================================================================
    # DEMAND FORECASTING TOOLS
    # ========================================================================
    
    def get_latest_forecasts(self) -> List[Dict[str, Any]]:
        """
        Get all latest demand forecasts from Module 4.
        
        Returns:
            List of forecasts for all categories
        """
        query = """
            SELECT 
                forecast_date,
                category,
                predicted_quantity,
                lower_bound,
                upper_bound,
                model_type as model,
                forecast_created_at
            FROM vw_latest_forecasts
            ORDER BY category, forecast_date
        """
        try:
            return self._execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get forecasts: {e}")
            return []
    
    def get_demand_forecast(self, category: str) -> List[Dict[str, Any]]:
        """
        Get demand forecast for a specific category.
        
        Args:
            category: Item category name (or 'Overall' for all categories)
            
        Returns:
            List of forecast periods for the category
        """
        query = """
            SELECT 
                forecast_date,
                category,
                predicted_quantity,
                lower_bound,
                upper_bound,
                model_type as model,
                forecast_created_at as created_at
            FROM vw_latest_forecasts
            WHERE LOWER(category) = LOWER(%s)
            ORDER BY forecast_date
        """
        try:
            return self._execute_query(query, (category,))
        except Exception as e:
            logger.error(f"Failed to get forecast for {category}: {e}")
            return []
    
    def get_overall_demand_forecast(self) -> List[Dict[str, Any]]:
        """
        Get overall demand forecast across all categories.
        
        Returns:
            Overall demand forecast periods
        """
        return self.get_demand_forecast('Overall')
    
    def get_forecast_summary(self) -> Dict[str, Any]:
        """
        Get summary of demand forecasts.
        
        Returns:
            Summary with total predicted demand, date range, categories
        """
        query = """
            SELECT 
                COUNT(DISTINCT category) as category_count,
                MIN(forecast_date) as first_forecast_date,
                MAX(forecast_date) as last_forecast_date,
                SUM(CASE WHEN category = 'Overall' THEN predicted_quantity ELSE 0 END) as total_predicted_demand,
                AVG(CASE WHEN category = 'Overall' THEN predicted_quantity ELSE NULL END) as avg_monthly_demand
            FROM vw_latest_forecasts
        """
        try:
            results = self._execute_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Failed to get forecast summary: {e}")
            return {}
    
    # ========================================================================
    # COMBINED INSIGHTS TOOLS
    # ========================================================================
    
    def get_supplier_full_insights(self, supplier_name: str) -> Dict[str, Any]:
        """
        Get comprehensive ML insights for a supplier.
        Combines score, anomalies, and relevant context.
        
        Args:
            supplier_name: Name of the supplier
            
        Returns:
            Dict with score, anomalies, and analysis
        """
        insights = {
            'supplier': supplier_name,
            'score': self.get_supplier_score(supplier_name),
            'anomalies': self.get_supplier_anomalies(supplier_name),
            'anomaly_count': 0,
            'has_score': False,
            'has_anomalies': False
        }
        
        if insights['score']:
            insights['has_score'] = True
        
        if insights['anomalies']:
            insights['has_anomalies'] = True
            insights['anomaly_count'] = len(insights['anomalies'])
        
        return insights
    
    def get_category_insights(self, category: str) -> Dict[str, Any]:
        """
        Get comprehensive ML insights for a category.
        Combines forecasts, anomalies, and supplier performance.
        
        Args:
            category: Item category name
            
        Returns:
            Dict with forecasts, anomalies, and top suppliers
        """
        insights = {
            'category': category,
            'forecast': self.get_demand_forecast(category),
            'anomalies': self.get_category_anomalies(category),
            'has_forecast': False,
            'has_anomalies': False
        }
        
        if insights['forecast']:
            insights['has_forecast'] = True
        
        if insights['anomalies']:
            insights['has_anomalies'] = True
            insights['anomaly_count'] = len(insights['anomalies'])
        
        return insights


# Singleton instance
ml_tools = MLTools()
