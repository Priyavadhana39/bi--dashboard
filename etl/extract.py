"""
Extract Module
Handles data extraction from raw CSV files.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extracts procurement data from CSV files."""
    
    def __init__(self, raw_data_path: str):
        """
        Initialize the DataExtractor.
        
        Args:
            raw_data_path: Path to the raw CSV file
        """
        self.raw_data_path = Path(raw_data_path)
        
    def validate_file_exists(self) -> bool:
        """
        Validate that the raw data file exists.
        
        Returns:
            True if file exists, False otherwise
        """
        if not self.raw_data_path.exists():
            logger.error(f"Raw data file not found: {self.raw_data_path}")
            return False
        
        if not self.raw_data_path.is_file():
            logger.error(f"Path is not a file: {self.raw_data_path}")
            return False
            
        logger.info(f"Raw data file validated: {self.raw_data_path}")
        return True
    
    def extract(self) -> Tuple[pd.DataFrame, dict]:
        """
        Extract data from the raw CSV file.
        
        Returns:
            Tuple of (DataFrame, extraction_metadata)
        """
        logger.info("Starting data extraction...")
        
        # Validate file exists
        if not self.validate_file_exists():
            raise FileNotFoundError(f"Raw data file not found: {self.raw_data_path}")
        
        # Read CSV file
        try:
            df = pd.read_csv(self.raw_data_path)
            logger.info(f"Successfully read CSV file: {self.raw_data_path}")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
        
        # Collect extraction metadata
        metadata = {
            'file_path': str(self.raw_data_path),
            'total_records': len(df),
            'total_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'file_size_bytes': self.raw_data_path.stat().st_size
        }
        
        logger.info(f"Extracted {metadata['total_records']} records with {metadata['total_columns']} columns")
        logger.info(f"Columns: {metadata['columns']}")
        
        return df, metadata
