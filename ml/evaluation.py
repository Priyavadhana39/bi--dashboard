"""
ML Evaluation Module
Evaluates and validates ML model results.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List
import json

logger = logging.getLogger(__name__)


class MLEvaluator:
    """Evaluates ML model results and performs validation."""
    
    def __init__(self):
        """Initialize ML evaluator."""
        self.evaluation_results = {}
    
    def evaluate_supplier_scoring(
        self, 
        scores_df: pd.DataFrame,
        validation_dict: dict
    ) -> Dict:
        """
        Evaluate supplier scoring results.
        
        Args:
            scores_df: DataFrame with supplier scores
            validation_dict: Validation results from scorer
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating supplier scoring results...")
        
        evaluation = {
            'component': 'Supplier Performance Scoring',
            'method': 'Weighted Composite Scoring',
            'total_suppliers': len(scores_df),
            'score_statistics': {
                'min': float(scores_df['supplier_score'].min()),
                'max': float(scores_df['supplier_score'].max()),
                'mean': float(scores_df['supplier_score'].mean()),
                'std': float(scores_df['supplier_score'].std()),
                'median': float(scores_df['supplier_score'].median())
            },
            'category_distribution': scores_df['performance_category'].value_counts().to_dict(),
            'top_supplier': {
                'name': scores_df.loc[scores_df['supplier_rank'] == 1, 'supplier'].values[0],
                'score': float(scores_df.loc[scores_df['supplier_rank'] == 1, 'supplier_score'].values[0]),
                'category': scores_df.loc[scores_df['supplier_rank'] == 1, 'performance_category'].values[0]
            },
            'bottom_supplier': {
                'name': scores_df.loc[scores_df['supplier_rank'] == len(scores_df), 'supplier'].values[0],
                'score': float(scores_df.loc[scores_df['supplier_rank'] == len(scores_df), 'supplier_score'].values[0]),
                'category': scores_df.loc[scores_df['supplier_rank'] == len(scores_df), 'performance_category'].values[0]
            },
            'validation': validation_dict,
            'sanity_checks': {
                'all_scores_in_range': (scores_df['supplier_score'] >= 0).all() and (scores_df['supplier_score'] <= 100).all(),
                'unique_ranks': scores_df['supplier_rank'].nunique() == len(scores_df),
                'no_null_scores': scores_df['supplier_score'].notna().all(),
                'categories_reasonable': set(scores_df['performance_category'].unique()).issubset({'Excellent', 'Good', 'Average', 'Poor'})
            }
        }
        
        # Overall pass/fail
        evaluation['passed'] = all(evaluation['sanity_checks'].values())
        
        self.evaluation_results['supplier_scoring'] = evaluation
        
        logger.info(f"Supplier scoring evaluation: {'PASSED' if evaluation['passed'] else 'FAILED'}")
        logger.info(f"Score range: {evaluation['score_statistics']['min']:.2f} - {evaluation['score_statistics']['max']:.2f}")
        logger.info(f"Category distribution: {evaluation['category_distribution']}")
        
        return evaluation
    
    def evaluate_anomaly_detection(
        self,
        anomalies_df: pd.DataFrame,
        summary_dict: dict
    ) -> Dict:
        """
        Evaluate price anomaly detection results.
        
        Args:
            anomalies_df: DataFrame with anomaly results
            summary_dict: Summary statistics from detector
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating anomaly detection results...")
        
        anomalies = anomalies_df[anomalies_df['anomaly_status'] == 'Anomaly']
        
        evaluation = {
            'component': 'Price Anomaly Detection',
            'method': 'Isolation Forest',
            'total_records': len(anomalies_df),
            'anomalies_detected': len(anomalies),
            'anomaly_percentage': float((len(anomalies) / len(anomalies_df) * 100) if len(anomalies_df) > 0 else 0),
            'anomaly_score_statistics': {
                'min': float(anomalies_df['anomaly_score'].min()),
                'max': float(anomalies_df['anomaly_score'].max()),
                'mean': float(anomalies_df['anomaly_score'].mean()),
                'anomaly_mean': float(anomalies['anomaly_score'].mean()) if len(anomalies) > 0 else None
            },
            'price_level_distribution': anomalies['price_level'].value_counts().to_dict() if len(anomalies) > 0 else {},
            'anomalies_by_supplier': summary_dict.get('anomaly_by_supplier', {}),
            'anomalies_by_category': summary_dict.get('anomaly_by_category', {}),
            'high_price_anomalies': summary_dict.get('high_price_anomalies', 0),
            'low_price_anomalies': summary_dict.get('low_price_anomalies', 0),
            'sanity_checks': {
                'reasonable_anomaly_rate': 1.0 <= (len(anomalies) / len(anomalies_df) * 100) <= 15.0,
                'anomaly_scores_present': anomalies_df['anomaly_score'].notna().all(),
                'status_values_valid': set(anomalies_df['anomaly_status'].unique()).issubset({'Normal', 'Anomaly'}),
                'price_levels_valid': set(anomalies['price_level'].unique()).issubset({'High', 'Low', 'Normal', 'Unknown'}) if len(anomalies) > 0 else True
            }
        }
        
        # Overall pass/fail
        evaluation['passed'] = all(evaluation['sanity_checks'].values())
        
        self.evaluation_results['anomaly_detection'] = evaluation
        
        logger.info(f"Anomaly detection evaluation: {'PASSED' if evaluation['passed'] else 'FAILED'}")
        logger.info(f"Detected {len(anomalies)} anomalies ({evaluation['anomaly_percentage']:.2f}%)")
        logger.info(f"Price level distribution: {evaluation['price_level_distribution']}")
        
        return evaluation
    
    def evaluate_demand_forecasting(
        self,
        forecasts_df: pd.DataFrame,
        metrics_dict: dict,
        summary_dict: dict
    ) -> Dict:
        """
        Evaluate demand forecasting results.
        
        Args:
            forecasts_df: DataFrame with forecasts
            metrics_dict: Forecast evaluation metrics
            summary_dict: Summary statistics
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating demand forecasting results...")
        
        overall_metrics = metrics_dict.get('overall', {})
        
        evaluation = {
            'component': 'Demand Forecasting',
            'method': 'Exponential Smoothing (Holt-Winters)',
            'forecast_periods': summary_dict.get('forecast_periods', 0),
            'total_forecasts': len(forecasts_df),
            'forecast_date_range': {
                'start': str(summary_dict.get('forecast_start', '')),
                'end': str(summary_dict.get('forecast_end', ''))
            },
            'categories_forecasted': summary_dict.get('categories', []),
            'prediction_statistics': {
                'total_predicted_quantity': summary_dict.get('total_predicted_quantity', 0),
                'avg_predicted_quantity': float(summary_dict.get('avg_predicted_quantity', 0))
            },
            'model_performance': {
                'MAE': float(overall_metrics.get('MAE', 0)),
                'RMSE': float(overall_metrics.get('RMSE', 0)),
                'MAPE': float(overall_metrics.get('MAPE')) if overall_metrics.get('MAPE') is not None else None
            },
            'category_metrics': metrics_dict.get('by_category', {}),
            'sanity_checks': {
                'forecasts_generated': len(forecasts_df) > 0,
                'no_negative_predictions': (forecasts_df['predicted_quantity'] >= 0).all(),
                'reasonable_mae': overall_metrics.get('MAE', float('inf')) < 100000,  # Should be reasonable
                'bounds_consistent': (forecasts_df['lower_bound'] <= forecasts_df['predicted_quantity']).all() if 'lower_bound' in forecasts_df.columns else True
            }
        }
        
        # Overall pass/fail
        evaluation['passed'] = all(evaluation['sanity_checks'].values())
        
        self.evaluation_results['demand_forecasting'] = evaluation
        
        logger.info(f"Demand forecasting evaluation: {'PASSED' if evaluation['passed'] else 'FAILED'}")
        logger.info(f"MAE: {evaluation['model_performance']['MAE']:.2f}")
        logger.info(f"RMSE: {evaluation['model_performance']['RMSE']:.2f}")
        if evaluation['model_performance']['MAPE'] is not None:
            logger.info(f"MAPE: {evaluation['model_performance']['MAPE']:.2f}%")
        
        return evaluation
    
    def generate_overall_report(self) -> Dict:
        """
        Generate overall evaluation report for all components.
        
        Returns:
            Dictionary with complete evaluation report
        """
        logger.info("Generating overall evaluation report...")
        
        components_passed = sum(1 for result in self.evaluation_results.values() if result.get('passed', False))
        total_components = len(self.evaluation_results)
        
        report = {
            'module': 'Module 4: Machine Learning & Predictive Analytics',
            'evaluation_summary': {
                'total_components': total_components,
                'components_passed': components_passed,
                'components_failed': total_components - components_passed,
                'overall_status': 'PASS' if components_passed == total_components else 'FAIL'
            },
            'component_results': self.evaluation_results,
            'recommendations': self._generate_recommendations()
        }
        
        logger.info(f"Overall status: {report['evaluation_summary']['overall_status']}")
        logger.info(f"Components passed: {components_passed}/{total_components}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on evaluation results.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Supplier scoring recommendations
        if 'supplier_scoring' in self.evaluation_results:
            scoring = self.evaluation_results['supplier_scoring']
            score_range = scoring['score_statistics']['max'] - scoring['score_statistics']['min']
            if score_range < 10:
                recommendations.append("Supplier scores are very close. Consider adjusting feature weights to better differentiate performance.")
        
        # Anomaly detection recommendations
        if 'anomaly_detection' in self.evaluation_results:
            anomaly = self.evaluation_results['anomaly_detection']
            if anomaly['anomaly_percentage'] > 10:
                recommendations.append(f"Anomaly rate is {anomaly['anomaly_percentage']:.1f}%, which is high. Consider adjusting contamination parameter.")
            if anomaly['anomaly_percentage'] < 2:
                recommendations.append(f"Anomaly rate is {anomaly['anomaly_percentage']:.1f}%, which is low. May need to increase contamination parameter.")
        
        # Forecasting recommendations
        if 'demand_forecasting' in self.evaluation_results:
            forecast = self.evaluation_results['demand_forecasting']
            mae = forecast['model_performance']['MAE']
            if mae > 10000:
                recommendations.append(f"Forecast MAE is {mae:.0f}, which is high. Consider collecting more historical data or trying different models.")
        
        if not recommendations:
            recommendations.append("All ML components performing well. Continue monitoring results.")
        
        return recommendations
    
    def save_report(self, filepath: str):
        """
        Save evaluation report to JSON file.
        
        Args:
            filepath: Path to save report
        """
        report = self.generate_overall_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Evaluation report saved to {filepath}")
    
    def print_summary(self):
        """Print a human-readable summary of evaluation results."""
        report = self.generate_overall_report()
        
        print("\n" + "="*80)
        print("ML EVALUATION SUMMARY")
        print("="*80)
        print(f"Overall Status: {report['evaluation_summary']['overall_status']}")
        print(f"Components Passed: {report['evaluation_summary']['components_passed']}/{report['evaluation_summary']['total_components']}")
        print()
        
        for component_name, component_result in report['component_results'].items():
            print(f"{component_result['component']}:")
            print(f"  Status: {'PASSED' if component_result['passed'] else 'FAILED'}")
            print(f"  Method: {component_result['method']}")
            
            if component_name == 'supplier_scoring':
                print(f"  Suppliers: {component_result['total_suppliers']}")
                print(f"  Score Range: {component_result['score_statistics']['min']:.2f} - {component_result['score_statistics']['max']:.2f}")
                print(f"  Top Supplier: {component_result['top_supplier']['name']} ({component_result['top_supplier']['score']:.2f})")
            
            elif component_name == 'anomaly_detection':
                print(f"  Records Analyzed: {component_result['total_records']}")
                print(f"  Anomalies: {component_result['anomalies_detected']} ({component_result['anomaly_percentage']:.2f}%)")
                print(f"  High Price: {component_result['high_price_anomalies']}, Low Price: {component_result['low_price_anomalies']}")
            
            elif component_name == 'demand_forecasting':
                print(f"  Forecasts Generated: {component_result['total_forecasts']}")
                print(f"  MAE: {component_result['model_performance']['MAE']:.2f}")
                print(f"  RMSE: {component_result['model_performance']['RMSE']:.2f}")
            
            print()
        
        print("Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        print("="*80 + "\n")
