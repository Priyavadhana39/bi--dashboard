"""
Pipeline Module
Orchestrates the complete ETL process.
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from etl.extract import DataExtractor
from etl.transform import DataTransformer
from etl.validate import DataValidator

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Orchestrates the complete ETL pipeline."""
    
    def __init__(
        self,
        raw_data_path: str,
        output_path: str,
        log_dir: str = "logs"
    ):
        """
        Initialize the ETL Pipeline.
        
        Args:
            raw_data_path: Path to the raw CSV file
            output_path: Path to save the processed CSV file
            log_dir: Directory to save logs
        """
        self.raw_data_path = raw_data_path
        self.output_path = output_path
        self.log_dir = Path(log_dir)
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.extractor = DataExtractor(raw_data_path)
        self.transformer = DataTransformer()
        self.validator = DataValidator()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging for the pipeline."""
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"etl_pipeline_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logger.info(f"Logging configured. Log file: {log_file}")
    
    def run(self, save_report: bool = True) -> pd.DataFrame:
        """
        Run the complete ETL pipeline.
        
        Args:
            save_report: Whether to save the validation report to file
            
        Returns:
            Processed DataFrame
        """
        logger.info("="*80)
        logger.info("STARTING ETL PIPELINE")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        try:
            # EXTRACT
            logger.info("\n--- PHASE 1: EXTRACTION ---")
            df_raw, extraction_metadata = self.extractor.extract()
            logger.info(f"Extraction completed: {extraction_metadata['total_records']} records")
            
            # TRANSFORM
            logger.info("\n--- PHASE 2: TRANSFORMATION ---")
            df_transformed, transformation_stats = self.transformer.transform(df_raw)
            logger.info(f"Transformation completed: {transformation_stats['records_after']} records")
            
            # VALIDATE
            logger.info("\n--- PHASE 3: VALIDATION ---")
            validation_report = self.validator.generate_validation_report(
                df_transformed,
                extraction_metadata,
                transformation_stats
            )
            logger.info("Validation completed")
            
            # LOAD (Save to file)
            logger.info("\n--- PHASE 4: LOAD ---")
            self._save_processed_data(df_transformed)
            logger.info(f"Processed data saved to: {self.output_path}")
            
            # Save validation report
            if save_report:
                report_path = self.log_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.validator.save_report_to_file(str(report_path))
                logger.info(f"Validation report saved to: {report_path}")
            
            # Print summary
            logger.info("\n--- PIPELINE SUMMARY ---")
            self.validator.print_report_summary()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"\nPipeline execution time: {duration:.2f} seconds")
            logger.info("="*80)
            logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("="*80)
            
            return df_transformed
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}", exc_info=True)
            raise
    
    def _save_processed_data(self, df: pd.DataFrame) -> None:
        """
        Save processed data to CSV file.
        
        Args:
            df: Processed DataFrame
        """
        try:
            df.to_csv(self.output_path, index=False)
            logger.info(f"Successfully saved {len(df)} records to {self.output_path}")
        except Exception as e:
            logger.error(f"Error saving processed data: {e}")
            raise
    
    def verify_raw_data_integrity(self) -> bool:
        """
        Verify that the raw data file was not modified.
        
        Returns:
            True if raw data is intact
        """
        logger.info("Verifying raw data integrity...")
        
        try:
            # Check if file exists
            if not Path(self.raw_data_path).exists():
                logger.error("Raw data file not found")
                return False
            
            # Read and count records
            df_raw = pd.read_csv(self.raw_data_path)
            logger.info(f"Raw data file intact: {len(df_raw)} records")
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying raw data: {e}")
            return False


def main():
    """Main entry point for the ETL pipeline."""
    # Define paths
    raw_data_path = "data/raw/Procurement KPI Analysis Dataset.csv"
    processed_data_path = "data/processed/procurement_cleaned.csv"
    log_dir = "logs"
    
    # Create and run pipeline
    pipeline = ETLPipeline(
        raw_data_path=raw_data_path,
        output_path=processed_data_path,
        log_dir=log_dir
    )
    
    # Run the pipeline
    df_processed = pipeline.run(save_report=True)
    
    # Verify raw data was not modified
    pipeline.verify_raw_data_integrity()
    
    print("\n✓ ETL Pipeline execution completed")
    print(f"✓ Processed data saved to: {processed_data_path}")
    print(f"✓ Raw data remains unchanged at: {raw_data_path}")
    print(f"✓ Logs saved to: {log_dir}/")


if __name__ == "__main__":
    main()
