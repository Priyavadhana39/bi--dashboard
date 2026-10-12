"""
Database Connection Module
Manages PostgreSQL database connections using environment variables.
"""

import os
import logging
from typing import Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages PostgreSQL database connections."""
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize database connection manager.
        
        Args:
            env_file: Path to the .env file with database credentials
        """
        # Load environment variables
        load_dotenv(env_file)
        
        # Database connection parameters
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'procurement_intelligence'),
            'user': os.getenv('DB_USER'),
            'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
            'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', 10))
        }
        
        # Add password only if provided (supports peer/trust authentication)
        password = os.getenv('DB_PASSWORD')
        if password:
            self.connection_params['password'] = password
        
        # Validate required parameters
        if not self.connection_params['user']:
            raise ValueError("DB_USER environment variable is required")
        
        # Connection pool (optional)
        self.connection_pool = None
        
        logger.info(f"Database connection configured: {self.connection_params['database']}@{self.connection_params['host']}")
    
    def get_connection(self):
        """
        Create and return a new database connection.
        
        Returns:
            psycopg2 connection object
        """
        try:
            conn = psycopg2.connect(**self.connection_params)
            logger.info("Database connection established")
            return conn
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"PostgreSQL version: {version[0]}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_sql_file(self, sql_file_path: str) -> None:
        """
        Execute SQL commands from a file.
        
        Args:
            sql_file_path: Path to the SQL file
        """
        logger.info(f"Executing SQL file: {sql_file_path}")
        
        try:
            # Read SQL file
            with open(sql_file_path, 'r') as f:
                sql_commands = f.read()
            
            # Execute SQL
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql_commands)
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"SQL file executed successfully: {sql_file_path}")
            
        except Exception as e:
            logger.error(f"Error executing SQL file: {e}")
            raise
    
    def create_connection_pool(self, min_conn: int = 1, max_conn: int = 10):
        """
        Create a connection pool for better performance.
        
        Args:
            min_conn: Minimum number of connections in pool
            max_conn: Maximum number of connections in pool
        """
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                **self.connection_params
            )
            logger.info(f"Connection pool created: {min_conn}-{max_conn} connections")
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    
    def get_pooled_connection(self):
        """
        Get a connection from the pool.
        
        Returns:
            psycopg2 connection object from pool
        """
        if not self.connection_pool:
            raise RuntimeError("Connection pool not initialized. Call create_connection_pool() first.")
        
        return self.connection_pool.getconn()
    
    def return_pooled_connection(self, conn):
        """
        Return a connection to the pool.
        
        Args:
            conn: Connection to return to pool
        """
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def close_connection_pool(self):
        """Close all connections in the pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Connection pool closed")


def get_database_config() -> dict:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dictionary with database configuration
    """
    load_dotenv()
    
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'procurement_intelligence'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }


def create_database_if_not_exists(db_name: str = None) -> bool:
    """
    Create the database if it doesn't exist.
    
    Args:
        db_name: Name of database to create (defaults to DB_NAME from env)
        
    Returns:
        True if database was created or already exists
    """
    load_dotenv()
    
    if not db_name:
        db_name = os.getenv('DB_NAME', 'procurement_intelligence')
    
    # Connect to default 'postgres' database to create new database
    connection_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': 'postgres',  # Connect to default database
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        conn = psycopg2.connect(**connection_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE {db_name}')
            logger.info(f"Database '{db_name}' created successfully")
        else:
            logger.info(f"Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test database connection
    try:
        db = DatabaseConnection()
        if db.test_connection():
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
    except Exception as e:
        print(f"✗ Error: {e}")
