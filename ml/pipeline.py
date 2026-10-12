"""
ML Pipeline Module
Orchestrates the complete Machine Learning workflow for Module 4.

Pipeline stages:
1. Data Loading
2. Data Preprocessing
3. Supplier Performance Scoring
4. Price Anomaly Detection
5. Demand Forecasting
6. Model Evaluation
7. Results Storage
8. Report Generation
"""

import logging
import os
from datetime import datetime
import json

from ml.data_loader import MLDataLoader
from ml.preprocessing import MLPreprocessor
from ml.supplier_scoring import SupplierScorer
from ml.price_anomaly import PriceAnomalyDetector
from ml.demand_forecasting import DemandForecaster
from ml.evaluation import MLEvaluator
from ml.ml_storage import MLStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ml_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class MLPipeline:
    """Complete ML pipeline for procurement intelligence."""
    
    def __init__(self, output_dir: str = 'ml/outputs'):
        """
        Initialize ML pipeline.
        
        Args:
            output_dir: Directory for saving outputs
        """
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize components
        self.data_loader = MLDataLoader()
        self.preprocessor = MLPreprocessor()
        self.storage = MLStorage()
        self.evaluator = MLEvaluator()
        
        # Results storage
        self.results = {
            'supplier_scores': None,
            'price_anomalies': None,
            'demand_forecasts': None,
            'metrics': {},
            'evaluation': None
        }
        
        logger.info(f"Initialized ML Pipeline (timestamp: {self.timestamp})")
    
    def run_complete_pipeline(self, save_to_db: bool = True) -> dict:
        """
        Run the complete ML pipeline.
        
        Args:
            save_to_db: Whether to save results to database
            
        Returns:
            Dictionary with pipeline results and statistics
        """
        logger.info("="*80)
        logger.info("STARTING ML PIPELINE")
        logger.info("="*80)
        
        pipeline_start = datetime.now()
        
        try:
            # Stage 1: Load Data
            logger.info("\n[STAGE 1/8] Loading data from PostgreSQL...")
            purchase_orders = self.data_loader.load_purchase_orders()
            supplier_aggregates = self.data_loader.load_supplier_aggregates()
            category_ts = self.data_loader.load_category_time_series()
            overall_ts = self.data_loader.load_overall_time_series()
            data_summary = self.data_loader.get_data_summary()
            logger.info(f"✓ Data loaded: {len(purchase_orders)} orders, {len(supplier_aggregates)} suppliers")
            
            # Stage 2: Setup Database Schema
            logger.info("\n[STAGE 2/8] Setting up ML database schema...")
            try:
                self.storage.setup_ml_schema('database/ml_schema.sql')
                logger.info("✓ ML schema ready")
            except Exception as e:
                logger.warning(f"Schema setup warning: {e} (may already exist)")
            
            # Stage 3: Supplier Performance Scoring
            logger.info("\n[STAGE 3/8] Running supplier performance scoring...")
            supplier_features = self.preprocessor.prepare_supplier_features(supplier_aggregates)
            scorer = SupplierScorer()
            supplier_scores = scorer.score_suppliers(supplier_features)
            supplier_validation = scorer.validate_scores(supplier_scores)
            self.results['supplier_scores'] = supplier_scores
            logger.info(f"✓ Scored {len(supplier_scores)} suppliers")
            
            # Evaluate supplier scoring
            supplier_eval = self.evaluator.evaluate_supplier_scoring(
                supplier_scores, 
                supplier_validation
            )
            
            # Stage 4: Price Anomaly Detection
            logger.info("\n[STAGE 4/8] Running price anomaly detection...")
            anomaly_features = self.preprocessor.prepare_anomaly_features(purchase_orders)
            detector = PriceAnomalyDetector(contamination=0.05)
            price_anomalies = detector.detect_anomalies(anomaly_features)
            anomaly_summary = detector.get_anomaly_summary(price_anomalies)
            self.results['price_anomalies'] = price_anomalies
            logger.info(f"✓ Analyzed {len(price_anomalies)} orders, detected {len(price_anomalies[price_anomalies['anomaly_status']=='Anomaly'])} anomalies")
            
            # Evaluate anomaly detection
            anomaly_eval = self.evaluator.evaluate_anomaly_detection(
                price_anomalies,
                anomaly_summary
            )
            
            # Stage 5: Demand Forecasting
            logger.info("\n[STAGE 5/8] Running demand forecasting...")
            forecaster = DemandForecaster(forecast_periods=3)
            
            # Overall forecast
            overall_forecast, overall_metrics = forecaster.forecast_overall(overall_ts, test_size=3)
            logger.info(f"✓ Generated overall forecast for next 3 months")
            
            # Category forecasts
            category_forecast, category_metrics = forecaster.forecast_by_category(category_ts, test_size=3)
            logger.info(f"✓ Generated category forecasts")
            
            # Combine forecasts
            import pandas as pd
            demand_forecasts = pd.concat([overall_forecast, category_forecast], ignore_index=True)
            self.results['demand_forecasts'] = demand_forecasts
            
            metrics = {
                'overall': overall_metrics,
                'by_category': category_metrics
            }
            self.results['metrics'] = metrics
            
            # Evaluate forecasting
            forecast_summary = forecaster.get_forecast_summary(demand_forecasts, metrics)
            forecast_eval = self.evaluator.evaluate_demand_forecasting(
                demand_forecasts,
                metrics,
                forecast_summary
            )
            
            # Stage 6: Generate Evaluation Report
            logger.info("\n[STAGE 6/8] Generating evaluation report...")
            evaluation_report = self.evaluator.generate_overall_report()
            self.results['evaluation'] = evaluation_report
            logger.info(f"✓ Evaluation complete: {evaluation_report['evaluation_summary']['overall_status']}")
            
            # Stage 7: Save Results
            logger.info("\n[STAGE 7/8] Saving results...")
            
            # Save to CSV
            supplier_scores.to_csv(f'{self.output_dir}/supplier_scores_{self.timestamp}.csv', index=False)
            price_anomalies.to_csv(f'{self.output_dir}/price_anomalies_{self.timestamp}.csv', index=False)
            demand_forecasts.to_csv(f'{self.output_dir}/demand_forecasts_{self.timestamp}.csv', index=False)
            logger.info(f"✓ Saved CSV outputs to {self.output_dir}/")
            
            # Save to database if requested
            if save_to_db:
                logger.info("Saving results to PostgreSQL...")
                self.storage.save_supplier_scores(supplier_scores)
                self.storage.save_price_anomalies(price_anomalies)
                self.storage.save_demand_forecasts(demand_forecasts)
                logger.info("✓ Results saved to database")
            
            # Save evaluation report
            self.evaluator.save_report(f'{self.output_dir}/evaluation_report_{self.timestamp}.json')
            
            # Stage 8: Generate Summary
            logger.info("\n[STAGE 8/8] Generating pipeline summary...")
            pipeline_end = datetime.now()
            pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
            
            summary = {
                'pipeline_status': 'SUCCESS',
                'timestamp': self.timestamp,
                'duration_seconds': pipeline_duration,
                'data_summary': data_summary,
                'results_summary': {
                    'suppliers_scored': len(supplier_scores),
                    'top_supplier': supplier_scores.loc[supplier_scores['supplier_rank']==1, 'supplier'].values[0],
                    'anomalies_detected': len(price_anomalies[price_anomalies['anomaly_status']=='Anomaly']),
                    'anomaly_percentage': float((len(price_anomalies[price_anomalies['anomaly_status']=='Anomaly']) / len(price_anomalies) * 100)),
                    'forecasts_generated': len(demand_forecasts),
                    'forecast_mae': overall_metrics['MAE'],
                    'forecast_rmse': overall_metrics['RMSE']
                },
                'evaluation_summary': evaluation_report['evaluation_summary'],
                'output_files': {
                    'supplier_scores': f'supplier_scores_{self.timestamp}.csv',
                    'price_anomalies': f'price_anomalies_{self.timestamp}.csv',
                    'demand_forecasts': f'demand_forecasts_{self.timestamp}.csv',
                    'evaluation_report': f'evaluation_report_{self.timestamp}.json'
                },
                'database_updated': save_to_db
            }
            
            # Save summary
            with open(f'{self.output_dir}/pipeline_summary_{self.timestamp}.json', 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info("="*80)
            logger.info("ML PIPELINE COMPLETED SUCCESSFULLY")
            logger.info(f"Duration: {pipeline_duration:.2f} seconds")
            logger.info(f"Status: {evaluation_report['evaluation_summary']['overall_status']}")
            logger.info(f"Components Passed: {evaluation_report['evaluation_summary']['components_passed']}/3")
            logger.info("="*80)
            
            # Print evaluation summary
            self.evaluator.print_summary()
            
            return summary
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            
            pipeline_end = datetime.now()
            pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
            
            summary = {
                'pipeline_status': 'FAILED',
                'timestamp': self.timestamp,
                'duration_seconds': pipeline_duration,
                'error': str(e),
                'error_type': type(e).__name__
            }
            
            # Save error summary
            with open(f'{self.output_dir}/pipeline_error_{self.timestamp}.json', 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.error("="*80)
            logger.error("ML PIPELINE FAILED")
            logger.error(f"Duration: {pipeline_duration:.2f} seconds")
            logger.error(f"Error: {e}")
            logger.error("="*80)
            
            raise
    
    def run_supplier_scoring_only(self) -> dict:
        """Run only supplier scoring component."""
        logger.info("Running supplier scoring component...")
        
        supplier_aggregates = self.data_loader.load_supplier_aggregates()
        supplier_features = self.preprocessor.prepare_supplier_features(supplier_aggregates)
        
        scorer = SupplierScorer()
        supplier_scores = scorer.score_suppliers(supplier_features)
        supplier_validation = scorer.validate_scores(supplier_scores)
        
        supplier_scores.to_csv(f'{self.output_dir}/supplier_scores_{self.timestamp}.csv', index=False)
        
        logger.info(f"✓ Supplier scoring complete: {len(supplier_scores)} suppliers scored")
        
        return {
            'scores': supplier_scores,
            'validation': supplier_validation
        }
    
    def run_anomaly_detection_only(self) -> dict:
        """Run only anomaly detection component."""
        logger.info("Running anomaly detection component...")
        
        purchase_orders = self.data_loader.load_purchase_orders()
        anomaly_features = self.preprocessor.prepare_anomaly_features(purchase_orders)
        
        detector = PriceAnomalyDetector(contamination=0.05)
        price_anomalies = detector.detect_anomalies(anomaly_features)
        anomaly_summary = detector.get_anomaly_summary(price_anomalies)
        
        price_anomalies.to_csv(f'{self.output_dir}/price_anomalies_{self.timestamp}.csv', index=False)
        
        logger.info(f"✓ Anomaly detection complete: {anomaly_summary['total_anomalies']} anomalies detected")
        
        return {
            'anomalies': price_anomalies,
            'summary': anomaly_summary
        }
    
    def run_forecasting_only(self) -> dict:
        """Run only demand forecasting component."""
        logger.info("Running demand forecasting component...")
        
        category_ts = self.data_loader.load_category_time_series()
        overall_ts = self.data_loader.load_overall_time_series()
        
        forecaster = DemandForecaster(forecast_periods=3)
        overall_forecast, overall_metrics = forecaster.forecast_overall(overall_ts, test_size=3)
        category_forecast, category_metrics = forecaster.forecast_by_category(category_ts, test_size=3)
        
        import pandas as pd
        demand_forecasts = pd.concat([overall_forecast, category_forecast], ignore_index=True)
        demand_forecasts.to_csv(f'{self.output_dir}/demand_forecasts_{self.timestamp}.csv', index=False)
        
        logger.info(f"✓ Forecasting complete: {len(demand_forecasts)} forecasts generated")
        
        return {
            'forecasts': demand_forecasts,
            'metrics': {
                'overall': overall_metrics,
                'by_category': category_metrics
            }
        }
    
    def get_results(self) -> dict:
        """Get pipeline results."""
        return self.results


def main():
    """Main entry point for ML pipeline."""
    import sys
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Parse command line arguments
    save_to_db = '--no-db' not in sys.argv
    
    # Run pipeline
    pipeline = MLPipeline()
    
    try:
        summary = pipeline.run_complete_pipeline(save_to_db=save_to_db)
        
        print("\n" + "="*80)
        print("PIPELINE SUMMARY")
        print("="*80)
        print(f"Status: {summary['pipeline_status']}")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Suppliers Scored: {summary['results_summary']['suppliers_scored']}")
        print(f"Top Supplier: {summary['results_summary']['top_supplier']}")
        print(f"Anomalies Detected: {summary['results_summary']['anomalies_detected']} ({summary['results_summary']['anomaly_percentage']:.2f}%)")
        print(f"Forecasts Generated: {summary['results_summary']['forecasts_generated']}")
        print(f"Forecast MAE: {summary['results_summary']['forecast_mae']:.2f}")
        print(f"Database Updated: {summary['database_updated']}")
        print(f"\nOutputs saved to: {pipeline.output_dir}/")
        print("="*80)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
