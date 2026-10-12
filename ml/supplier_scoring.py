"""
Supplier Performance Scoring Module

Uses a weighted scoring methodology to evaluate supplier performance.
This is an unsupervised approach since there are no ground-truth performance labels.

Scoring Methodology:
- Weighted composite score based on multiple performance dimensions
- Features: savings, lead time, quality, compliance, data completeness
- Each feature normalized and weighted according to business importance
- Final score ranks suppliers from best to worst
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SupplierScorer:
    """Scores supplier performance using weighted composite methodology."""
    
    def __init__(self):
        """
        Initialize supplier scorer with default weights.
        
        Weights represent business priorities:
        - Savings: 30% (cost reduction is critical)
        - Quality: 25% (low defects important)
        - Lead Time: 20% (timely delivery matters)
        - Compliance: 15% (regulatory/contractual adherence)
        - Data Completeness: 10% (transparency/tracking)
        """
        self.weights = {
            'savings_score': 0.30,
            'quality_score': 0.25,
            'lead_time_score': 0.20,
            'compliance_score': 0.15,
            'data_completeness_pct': 0.10
        }
        
        self.feature_columns = list(self.weights.keys())
        
        logger.info("Initialized SupplierScorer with weights:")
        for feature, weight in self.weights.items():
            logger.info(f"  {feature}: {weight:.0%}")
    
    def set_weights(self, weights: dict):
        """
        Set custom weights for scoring.
        
        Args:
            weights: Dictionary mapping feature names to weights (must sum to 1.0)
        """
        if not np.isclose(sum(weights.values()), 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {sum(weights.values())}")
        
        self.weights = weights
        self.feature_columns = list(weights.keys())
        logger.info("Updated weights")
    
    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize features to 0-100 scale.
        
        Args:
            df: DataFrame with raw feature scores
            
        Returns:
            DataFrame with normalized features
        """
        df = df.copy()
        
        for col in self.feature_columns:
            if col in df.columns and df[col].notna().any():
                # Min-max normalization to 0-100 scale
                min_val = df[col].min()
                max_val = df[col].max()
                
                if max_val > min_val:
                    df[f'{col}_normalized'] = ((df[col] - min_val) / (max_val - min_val)) * 100
                else:
                    # All values same, set to 50 (neutral)
                    df[f'{col}_normalized'] = 50.0
                
                logger.debug(f"Normalized {col}: [{min_val:.2f}, {max_val:.2f}] -> [0, 100]")
        
        return df
    
    def calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate weighted composite performance score.
        
        Handles missing values by adjusting weights proportionally.
        If a supplier is missing quality data, the other features get proportionally
        more weight in the final score.
        
        Args:
            df: DataFrame with normalized features
            
        Returns:
            DataFrame with composite scores
        """
        df = df.copy()
        
        # Calculate weighted score
        df['composite_score'] = 0.0
        df['weight_sum'] = 0.0
        
        for feature, weight in self.weights.items():
            normalized_col = f'{feature}_normalized'
            
            if normalized_col in df.columns:
                # Add weighted contribution (only for non-null values)
                df['composite_score'] += df[normalized_col].fillna(0) * weight * df[normalized_col].notna()
                df['weight_sum'] += weight * df[normalized_col].notna()
        
        # Adjust for missing data: divide by actual weight sum
        # This ensures suppliers aren't penalized for missing data that others also don't have
        df['composite_score'] = np.where(
            df['weight_sum'] > 0,
            df['composite_score'] / df['weight_sum'],
            0
        )
        
        logger.info(f"Calculated composite scores: {df['composite_score'].min():.2f} to {df['composite_score'].max():.2f}")
        
        return df
    
    def assign_ranks_and_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign ranks and performance categories based on scores.
        
        Performance categories:
        - Excellent: Top 20% (score >= 80th percentile)
        - Good: Next 30% (score >= 50th percentile)
        - Average: Next 30% (score >= 20th percentile)
        - Poor: Bottom 20% (score < 20th percentile)
        
        Args:
            df: DataFrame with composite scores
            
        Returns:
            DataFrame with ranks and categories
        """
        df = df.copy()
        
        # Assign ranks (1 = best)
        df['supplier_rank'] = df['composite_score'].rank(ascending=False, method='min').astype(int)
        
        # Calculate percentiles for categorization
        p80 = df['composite_score'].quantile(0.80)
        p50 = df['composite_score'].quantile(0.50)
        p20 = df['composite_score'].quantile(0.20)
        
        # Assign categories
        def categorize(score):
            if score >= p80:
                return 'Excellent'
            elif score >= p50:
                return 'Good'
            elif score >= p20:
                return 'Average'
            else:
                return 'Poor'
        
        df['performance_category'] = df['composite_score'].apply(categorize)
        
        # Log distribution
        category_counts = df['performance_category'].value_counts()
        logger.info("Performance category distribution:")
        for category, count in category_counts.items():
            logger.info(f"  {category}: {count} suppliers")
        
        return df
    
    def score_suppliers(self, supplier_df: pd.DataFrame) -> pd.DataFrame:
        """
        Complete supplier scoring pipeline.
        
        Args:
            supplier_df: DataFrame with supplier features (from preprocessing)
            
        Returns:
            DataFrame with scores, ranks, and categories
        """
        logger.info(f"Scoring {len(supplier_df)} suppliers...")
        
        # Step 1: Normalize features
        df = self.normalize_features(supplier_df)
        
        # Step 2: Calculate composite score
        df = self.calculate_composite_score(df)
        
        # Step 3: Assign ranks and categories
        df = self.assign_ranks_and_categories(df)
        
        # Select output columns
        output_cols = [
            'supplier_id',
            'supplier',
            'composite_score',
            'supplier_rank',
            'performance_category',
            'total_orders',
            'total_cost',
            'total_savings',
            'avg_savings_percentage',
            'avg_lead_time_days',
            'avg_defect_rate',
            'compliance_rate',
            'data_completeness_pct'
        ]
        
        result = df[output_cols].copy()
        result = result.rename(columns={'composite_score': 'supplier_score'})
        
        # Round numeric columns
        result['supplier_score'] = result['supplier_score'].round(2)
        result['avg_savings_percentage'] = result['avg_savings_percentage'].round(2)
        result['avg_lead_time_days'] = result['avg_lead_time_days'].round(2)
        result['avg_defect_rate'] = result['avg_defect_rate'].round(2)
        result['compliance_rate'] = result['compliance_rate'].round(2)
        result['data_completeness_pct'] = result['data_completeness_pct'].round(2)
        
        logger.info("Supplier scoring complete!")
        logger.info(f"Score range: {result['supplier_score'].min():.2f} - {result['supplier_score'].max():.2f}")
        logger.info(f"Top supplier: {result.loc[result['supplier_rank'] == 1, 'supplier'].values[0]} (score: {result.loc[result['supplier_rank'] == 1, 'supplier_score'].values[0]:.2f})")
        
        return result
    
    def get_feature_contributions(self, supplier_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate each feature's contribution to the final score.
        
        Useful for explainability: shows why a supplier got their score.
        
        Args:
            supplier_df: DataFrame with supplier features
            
        Returns:
            DataFrame with feature contributions per supplier
        """
        df = self.normalize_features(supplier_df)
        
        contributions = pd.DataFrame()
        contributions['supplier'] = df['supplier']
        contributions['supplier_id'] = df['supplier_id']
        
        for feature, weight in self.weights.items():
            normalized_col = f'{feature}_normalized'
            if normalized_col in df.columns:
                contributions[f'{feature}_contribution'] = df[normalized_col] * weight
        
        return contributions
    
    def validate_scores(self, result_df: pd.DataFrame) -> dict:
        """
        Validate scoring results with sanity checks.
        
        Args:
            result_df: DataFrame with scoring results
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'total_suppliers': len(result_df),
            'score_range_valid': (result_df['supplier_score'].min() >= 0 and 
                                  result_df['supplier_score'].max() <= 100),
            'ranks_unique': result_df['supplier_rank'].nunique() == len(result_df),
            'categories_present': result_df['performance_category'].nunique() >= 2,
            'no_null_scores': result_df['supplier_score'].notna().all(),
            'top_supplier': result_df.loc[result_df['supplier_rank'] == 1, 'supplier'].values[0],
            'bottom_supplier': result_df.loc[result_df['supplier_rank'] == len(result_df), 'supplier'].values[0],
        }
        
        validation['all_checks_passed'] = all([
            validation['score_range_valid'],
            validation['ranks_unique'],
            validation['categories_present'],
            validation['no_null_scores']
        ])
        
        return validation


def score_suppliers_pipeline(supplier_df: pd.DataFrame, weights: dict = None) -> Tuple[pd.DataFrame, dict]:
    """
    Convenience function to run complete supplier scoring pipeline.
    
    Args:
        supplier_df: DataFrame with supplier features
        weights: Optional custom weights
        
    Returns:
        Tuple of (scored_df, validation_dict)
    """
    scorer = SupplierScorer()
    
    if weights:
        scorer.set_weights(weights)
    
    result = scorer.score_suppliers(supplier_df)
    validation = scorer.validate_scores(result)
    
    return result, validation
