"""
Demand Forecasting Module

Forecasts future procurement demand (quantity) using time series methods.

Methodology:
- Exponential Smoothing (Holt-Winters) for seasonal patterns
- Monthly aggregation level
- Time-based train/test split (NO random shuffling)
- Evaluation using MAE, RMSE, MAPE
- Generates forecast with confidence intervals

Why Exponential Smoothing:
- Works well with limited historical data (2 years)
- Captures trend and seasonality
- Computationally efficient
- Provides prediction intervals
- More robust than ARIMA for short series
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class DemandForecaster:
    """Forecasts procurement demand using Exponential Smoothing."""
    
    def __init__(self, forecast_periods: int = 3):
        """
        Initialize demand forecaster.
        
        Args:
            forecast_periods: Number of periods to forecast ahead (default 3 months)
        """
        self.forecast_periods = forecast_periods
        self.models = {}
        self.forecasts = {}
        
        logger.info(f"Initialized DemandForecaster with forecast_periods={forecast_periods}")
    
    def prepare_series(self, df: pd.DataFrame, value_col: str = 'total_quantity') -> pd.Series:
        """
        Prepare time series for forecasting.
        
        Args:
            df: DataFrame with time series data (indexed by date or with date column)
            value_col: Column name for values to forecast
            
        Returns:
            Time series as pandas Series
        """
        # Ensure we have a datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'month_date' in df.columns:
                df = df.set_index('month_date')
            else:
                raise ValueError("DataFrame must have DatetimeIndex or 'month_date' column")
        
        series = df[value_col].copy()
        
        # Ensure no negative values
        if (series < 0).any():
            logger.warning("Negative values found in series, setting to 0")
            series = series.clip(lower=0)
        
        logger.info(f"Prepared series: {len(series)} periods, range {series.min():.0f} to {series.max():.0f}")
        
        return series
    
    def split_series(
        self, 
        series: pd.Series, 
        test_size: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Split time series into train and test sets.
        
        IMPORTANT: Uses time-based split, NOT random shuffling.
        
        Args:
            series: Time series to split
            test_size: Number of periods for test set
            
        Returns:
            Tuple of (train_series, test_series)
        """
        if len(series) <= test_size:
            raise ValueError(f"Series length ({len(series)}) must be > test_size ({test_size})")
        
        split_point = len(series) - test_size
        
        train = series.iloc[:split_point]
        test = series.iloc[split_point:]
        
        logger.info(f"Split series: train={len(train)} periods, test={len(test)} periods")
        logger.info(f"Train range: {train.index.min()} to {train.index.max()}")
        logger.info(f"Test range: {test.index.min()} to {test.index.max()}")
        
        return train, test
    
    def fit_exponential_smoothing(
        self, 
        train_series: pd.Series,
        seasonal_periods: int = 12,
        trend: str = 'add',
        seasonal: str = 'add'
    ) -> ExponentialSmoothing:
        """
        Fit Exponential Smoothing model.
        
        Args:
            train_series: Training time series
            seasonal_periods: Length of seasonal cycle (12 for monthly data)
            trend: Type of trend component ('add', 'mul', or None)
            seasonal: Type of seasonal component ('add', 'mul', or None)
            
        Returns:
            Fitted Exponential Smoothing model
        """
        logger.info(f"Fitting Exponential Smoothing (trend={trend}, seasonal={seasonal}, periods={seasonal_periods})...")
        
        # Check if we have enough data for seasonal model
        if len(train_series) < 2 * seasonal_periods:
            logger.warning(f"Insufficient data for seasonal model ({len(train_series)} < {2*seasonal_periods}), using simple model")
            seasonal = None
        
        try:
            model = ExponentialSmoothing(
                train_series,
                trend=trend,
                seasonal=seasonal,
                seasonal_periods=seasonal_periods if seasonal else None
            )
            
            fitted_model = model.fit(optimized=True)
            
            logger.info("Model fitted successfully")
            return fitted_model
            
        except Exception as e:
            logger.error(f"Failed to fit seasonal model: {e}")
            logger.info("Falling back to simple exponential smoothing")
            
            # Fallback to simple model
            model = ExponentialSmoothing(train_series, trend='add', seasonal=None)
            fitted_model = model.fit(optimized=True)
            
            return fitted_model
    
    def evaluate_forecast(
        self, 
        actual: pd.Series, 
        predicted: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate forecast evaluation metrics.
        
        Args:
            actual: Actual values
            predicted: Predicted values
            
        Returns:
            Dictionary with MAE, RMSE, MAPE
        """
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        
        # MAPE: only calculate if no zero values (division by zero issue)
        if (actual == 0).any():
            logger.warning("Zero values in actual data, MAPE not calculated")
            mape = np.nan
        else:
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        metrics = {
            'MAE': float(mae),
            'RMSE': float(rmse),
            'MAPE': float(mape) if not np.isnan(mape) else None
        }
        
        logger.info(f"Evaluation metrics: MAE={mae:.2f}, RMSE={rmse:.2f}" + 
                   (f", MAPE={mape:.2f}%" if not np.isnan(mape) else ""))
        
        return metrics
    
    def forecast_overall(
        self, 
        ts_df: pd.DataFrame,
        test_size: int = 3
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Forecast overall procurement demand.
        
        Args:
            ts_df: DataFrame with overall time series
            test_size: Number of periods for testing
            
        Returns:
            Tuple of (forecast_df, metrics_dict)
        """
        logger.info("Forecasting overall procurement demand...")
        
        # Prepare series
        series = self.prepare_series(ts_df, 'total_quantity')
        
        # Split
        train, test = self.split_series(series, test_size)
        
        # Fit model
        model = self.fit_exponential_smoothing(train)
        self.models['overall'] = model
        
        # Predict on test set
        test_predictions = model.forecast(steps=len(test))
        test_predictions = pd.Series(test_predictions, index=test.index)
        
        # Evaluate
        metrics = self.evaluate_forecast(test, test_predictions)
        
        # Generate future forecast
        future_forecast = model.forecast(steps=self.forecast_periods)
        
        # Create forecast dates
        last_date = series.index[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=self.forecast_periods,
            freq='MS'
        )
        
        # Build forecast dataframe
        forecast_df = pd.DataFrame({
            'forecast_date': forecast_dates,
            'category': 'Overall',
            'predicted_quantity': future_forecast.round(0).astype(int),
            'model': 'Exponential Smoothing'
        })
        
        # Add confidence intervals (approximation based on forecast variance)
        forecast_std = test_predictions.std()
        forecast_df['lower_bound'] = (forecast_df['predicted_quantity'] - 1.96 * forecast_std).clip(lower=0).round(0).astype(int)
        forecast_df['upper_bound'] = (forecast_df['predicted_quantity'] + 1.96 * forecast_std).round(0).astype(int)
        
        self.forecasts['overall'] = forecast_df
        
        logger.info(f"Overall forecast complete. Next 3 months: {forecast_df['predicted_quantity'].values}")
        
        return forecast_df, metrics
    
    def forecast_by_category(
        self,
        ts_df: pd.DataFrame,
        test_size: int = 3
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Forecast demand by category.
        
        Args:
            ts_df: DataFrame with category-level time series
            test_size: Number of periods for testing
            
        Returns:
            Tuple of (forecast_df, metrics_dict)
        """
        logger.info("Forecasting by category...")
        
        categories = ts_df['item_category'].unique()
        logger.info(f"Found {len(categories)} categories")
        
        all_forecasts = []
        all_metrics = {}
        
        for category in categories:
            logger.info(f"\nProcessing category: {category}")
            
            # Filter to category
            cat_df = ts_df[ts_df['item_category'] == category].copy()
            cat_df = cat_df.set_index('month_date') if 'month_date' in cat_df.columns else cat_df
            
            # Prepare series
            series = self.prepare_series(cat_df, 'total_quantity')
            
            # Check if we have enough data
            if len(series) <= test_size:
                logger.warning(f"Insufficient data for {category}, skipping")
                continue
            
            try:
                # Split
                train, test = self.split_series(series, test_size)
                
                # Fit model
                model = self.fit_exponential_smoothing(train, seasonal_periods=12)
                self.models[category] = model
                
                # Predict on test set
                test_predictions = model.forecast(steps=len(test))
                test_predictions = pd.Series(test_predictions, index=test.index)
                
                # Evaluate
                metrics = self.evaluate_forecast(test, test_predictions)
                all_metrics[category] = metrics
                
                # Generate future forecast
                future_forecast = model.forecast(steps=self.forecast_periods)
                
                # Create forecast dates
                last_date = series.index[-1]
                forecast_dates = pd.date_range(
                    start=last_date + pd.DateOffset(months=1),
                    periods=self.forecast_periods,
                    freq='MS'
                )
                
                # Build forecast dataframe
                cat_forecast_df = pd.DataFrame({
                    'forecast_date': forecast_dates,
                    'category': category,
                    'predicted_quantity': future_forecast.round(0).astype(int),
                    'model': 'Exponential Smoothing'
                })
                
                # Add confidence intervals
                forecast_std = test_predictions.std()
                cat_forecast_df['lower_bound'] = (cat_forecast_df['predicted_quantity'] - 1.96 * forecast_std).clip(lower=0).round(0).astype(int)
                cat_forecast_df['upper_bound'] = (cat_forecast_df['predicted_quantity'] + 1.96 * forecast_std).round(0).astype(int)
                
                all_forecasts.append(cat_forecast_df)
                
                logger.info(f"{category} forecast: {cat_forecast_df['predicted_quantity'].values}")
                
            except Exception as e:
                logger.error(f"Failed to forecast {category}: {e}")
                continue
        
        if not all_forecasts:
            raise ValueError("No successful category forecasts generated")
        
        # Combine all category forecasts
        forecast_df = pd.concat(all_forecasts, ignore_index=True)
        
        self.forecasts['by_category'] = forecast_df
        
        logger.info(f"\nCategory forecasting complete. Generated forecasts for {len(all_forecasts)} categories")
        
        return forecast_df, all_metrics
    
    def get_forecast_summary(self, forecast_df: pd.DataFrame, metrics: Dict) -> Dict:
        """
        Generate summary of forecast results.
        
        Args:
            forecast_df: DataFrame with forecasts
            metrics: Dictionary with evaluation metrics
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total_forecasts': len(forecast_df),
            'forecast_periods': self.forecast_periods,
            'forecast_start': forecast_df['forecast_date'].min(),
            'forecast_end': forecast_df['forecast_date'].max(),
            'avg_predicted_quantity': float(forecast_df['predicted_quantity'].mean()),
            'total_predicted_quantity': int(forecast_df['predicted_quantity'].sum()),
            'metrics': metrics
        }
        
        if 'category' in forecast_df.columns:
            summary['categories'] = forecast_df['category'].unique().tolist()
        
        return summary


def forecast_demand(
    overall_ts_df: pd.DataFrame,
    category_ts_df: pd.DataFrame = None,
    forecast_periods: int = 3,
    test_size: int = 3
) -> Tuple[pd.DataFrame, Dict, Dict]:
    """
    Convenience function to run complete demand forecasting pipeline.
    
    Args:
        overall_ts_df: DataFrame with overall time series
        category_ts_df: Optional DataFrame with category-level time series
        forecast_periods: Number of periods to forecast
        test_size: Number of periods for testing
        
    Returns:
        Tuple of (forecast_df, metrics_dict, summary_dict)
    """
    forecaster = DemandForecaster(forecast_periods=forecast_periods)
    
    # Forecast overall
    overall_forecast, overall_metrics = forecaster.forecast_overall(overall_ts_df, test_size)
    
    # Forecast by category if provided
    if category_ts_df is not None:
        category_forecast, category_metrics = forecaster.forecast_by_category(category_ts_df, test_size)
        
        # Combine forecasts
        forecast_df = pd.concat([overall_forecast, category_forecast], ignore_index=True)
        
        # Combine metrics
        metrics = {
            'overall': overall_metrics,
            'by_category': category_metrics
        }
    else:
        forecast_df = overall_forecast
        metrics = {'overall': overall_metrics}
    
    # Generate summary
    summary = forecaster.get_forecast_summary(forecast_df, metrics)
    
    return forecast_df, metrics, summary
