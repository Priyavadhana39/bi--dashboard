"""
ML Storage Module
Handles saving and loading ML results to/from PostgreSQL.
"""

import pandas as pd
import logging
from database.connection import DatabaseConnection
from datetime import datetime

logger = logging.getLogger(__name__)


class MLStorage:
    """Manages storage of ML results in PostgreSQL."""
    
    def __init__(self):
        """Initialize ML storage."""
        self.db = DatabaseConnection()
    
    def setup_ml_schema(self, schema_file: str = 'database/ml_schema.sql'):
        """
        Create ML tables in database.
        
        Args:
            schema_file: Path to SQL schema file
        """
        logger.info("Setting up ML schema...")
        
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(schema_sql)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info("ML schema created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create ML schema: {e}")
            raise
    
    def save_supplier_scores(self, scores_df: pd.DataFrame) -> int:
        """
        Save supplier scores to database.
        
        Args:
            scores_df: DataFrame with supplier scores
            
        Returns:
            Number of records inserted
        """
        logger.info(f"Saving {len(scores_df)} supplier scores...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        scoring_date = datetime.now()
        
        insert_query = """
        INSERT INTO ml_supplier_scores (
            supplier_id, supplier_score, supplier_rank, performance_category,
            total_orders, total_cost, total_savings, avg_savings_percentage,
            avg_lead_time_days, avg_defect_rate, compliance_rate,
            data_completeness_pct, scoring_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        rows_inserted = 0
        for _, row in scores_df.iterrows():
            cursor.execute(insert_query, (
                int(row['supplier_id']),
                float(row['supplier_score']),
                int(row['supplier_rank']),
                row['performance_category'],
                int(row['total_orders']),
                float(row['total_cost']),
                float(row['total_savings']),
                float(row['avg_savings_percentage']) if pd.notna(row['avg_savings_percentage']) else None,
                float(row['avg_lead_time_days']) if pd.notna(row['avg_lead_time_days']) else None,
                float(row['avg_defect_rate']) if pd.notna(row['avg_defect_rate']) else None,
                float(row['compliance_rate']) if pd.notna(row['compliance_rate']) else None,
                float(row['data_completeness_pct']) if pd.notna(row['data_completeness_pct']) else None,
                scoring_date
            ))
            rows_inserted += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Saved {rows_inserted} supplier scores")
        return rows_inserted
    
    def save_price_anomalies(self, anomalies_df: pd.DataFrame) -> int:
        """
        Save price anomalies to database.
        
        Args:
            anomalies_df: DataFrame with detected anomalies
            
        Returns:
            Number of records inserted
        """
        logger.info(f"Saving {len(anomalies_df)} anomaly records...")
        
        # Need to get supplier_id and category_id
        conn = self.db.get_connection()
        
        # Get mappings
        supplier_map = pd.read_sql("SELECT supplier_id, supplier_name FROM suppliers", conn)
        category_map = pd.read_sql("SELECT category_id, category_name FROM item_categories", conn)
        
        # Merge to get IDs
        df = anomalies_df.merge(supplier_map, left_on='supplier', right_on='supplier_name', how='left')
        df = df.merge(category_map, left_on='item_category', right_on='category_name', how='left')
        
        cursor = conn.cursor()
        
        detection_date = datetime.now()
        
        insert_query = """
        INSERT INTO ml_price_anomalies (
            po_id, supplier_id, category_id, order_date, quantity,
            unit_price, negotiated_price, total_cost, savings_percentage,
            anomaly_score, anomaly_status, price_level, detection_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        rows_inserted = 0
        for _, row in df.iterrows():
            cursor.execute(insert_query, (
                row['po_id'],
                int(row['supplier_id']),
                int(row['category_id']),
                row['order_date'],
                int(row['quantity']),
                float(row['unit_price']),
                float(row['negotiated_price']),
                float(row['total_cost']),
                float(row['savings_percentage']) if pd.notna(row['savings_percentage']) else None,
                float(row['anomaly_score']),
                row['anomaly_status'],
                row['price_level'],
                detection_date
            ))
            rows_inserted += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Saved {rows_inserted} anomaly records")
        return rows_inserted
    
    def save_demand_forecasts(self, forecasts_df: pd.DataFrame) -> int:
        """
        Save demand forecasts to database.
        
        Args:
            forecasts_df: DataFrame with forecasts
            
        Returns:
            Number of records inserted
        """
        logger.info(f"Saving {len(forecasts_df)} forecast records...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        forecast_created_at = datetime.now()
        
        insert_query = """
        INSERT INTO ml_demand_forecasts (
            forecast_date, category, predicted_quantity, lower_bound,
            upper_bound, model_type, forecast_created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        rows_inserted = 0
        for _, row in forecasts_df.iterrows():
            cursor.execute(insert_query, (
                row['forecast_date'],
                row['category'],
                int(row['predicted_quantity']),
                int(row['lower_bound']) if pd.notna(row['lower_bound']) else None,
                int(row['upper_bound']) if pd.notna(row['upper_bound']) else None,
                row['model'],
                forecast_created_at
            ))
            rows_inserted += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Saved {rows_inserted} forecast records")
        return rows_inserted
    
    def load_latest_supplier_scores(self) -> pd.DataFrame:
        """
        Load latest supplier scores from database.
        
        Returns:
            DataFrame with latest scores
        """
        logger.info("Loading latest supplier scores...")
        
        query = "SELECT * FROM vw_latest_supplier_scores"
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Loaded {len(df)} supplier scores")
        return df
    
    def load_active_anomalies(self) -> pd.DataFrame:
        """
        Load active price anomalies from database.
        
        Returns:
            DataFrame with anomalies
        """
        logger.info("Loading active anomalies...")
        
        query = "SELECT * FROM vw_active_anomalies"
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Loaded {len(df)} anomalies")
        return df
    
    def load_latest_forecasts(self) -> pd.DataFrame:
        """
        Load latest demand forecasts from database.
        
        Returns:
            DataFrame with forecasts
        """
        logger.info("Loading latest forecasts...")
        
        query = "SELECT * FROM vw_latest_forecasts"
        
        conn = self.db.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Loaded {len(df)} forecasts")
        return df
    
    def clear_old_results(self, days_to_keep: int = 30):
        """
        Clear old ML results to prevent table bloat.
        
        Args:
            days_to_keep: Number of days of results to keep
        """
        logger.info(f"Clearing results older than {days_to_keep} days...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Clear old supplier scores
        cursor.execute("""
            DELETE FROM ml_supplier_scores 
            WHERE scoring_date < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """, (days_to_keep,))
        
        # Clear old anomalies
        cursor.execute("""
            DELETE FROM ml_price_anomalies 
            WHERE detection_date < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """, (days_to_keep,))
        
        # Clear old forecasts
        cursor.execute("""
            DELETE FROM ml_demand_forecasts 
            WHERE forecast_created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """, (days_to_keep,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Old results cleared")
