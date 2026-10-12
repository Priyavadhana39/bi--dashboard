# Module 4: Machine Learning & Predictive Analytics

## Overview

Module 4 adds genuine machine learning capabilities to the Procurement Intelligence System. It provides three core ML components that generate actionable insights from historical procurement data.

**Module Status:** ✅ Complete and Verified

## Components

### 1. Supplier Performance Scoring
- **Method:** Weighted Composite Scoring (Unsupervised)
- **Purpose:** Rank suppliers based on multiple performance dimensions
- **Output:** Scores (0-100), ranks (1=best), categories (Excellent/Good/Average/Poor)

### 2. Price Anomaly Detection
- **Method:** Isolation Forest (Unsupervised)
- **Purpose:** Identify unusual procurement prices
- **Output:** Anomaly scores, status (Normal/Anomaly), price level (High/Low)

### 3. Demand Forecasting
- **Method:** Exponential Smoothing (Holt-Winters)
- **Purpose:** Forecast future procurement demand
- **Output:** Monthly quantity predictions with confidence intervals

---

## Architecture

```
ml/
├── __init__.py                  # Module initialization
├── data_loader.py               # Data loading from PostgreSQL
├── preprocessing.py             # Feature engineering & data prep
├── supplier_scoring.py          # Supplier performance scoring
├── price_anomaly.py             # Price anomaly detection
├── demand_forecasting.py        # Demand forecasting
├── evaluation.py                # Model evaluation & validation
├── ml_storage.py                # Save/load results to/from DB
├── pipeline.py                  # Complete ML pipeline orchestration
├── outputs/                     # Generated results (CSV, JSON)
├── models/                      # Saved models (if needed)
└── README_ML.md                 # This file

database/
└── ml_schema.sql                # ML results database schema
```

---

## Data Requirements

### Input Data
- **Purchase Orders:** 777 records from PostgreSQL
- **Date Range:** 2022-01-01 to 2024-01-01
- **Suppliers:** 5 suppliers
- **Categories:** 5 item categories

### Data Quality Handling

**CRITICAL RULES:**
1. ✅ Missing `defective_units` → **NOT treated as zero defects**
2. ✅ Missing `delivery_date` → **NOT treated as successful delivery**
3. ✅ Time series → **Time-based split, NEVER random shuffle**
4. ✅ Anomaly detection → **No data leakage in feature engineering**

### Missing Data Statistics
- **Missing Delivery Dates:** 87 orders (11.2%)
- **Missing Defect Data:** 136 orders (17.5%)

**Approach:** Features are calculated only from available data. Missing values are either:
- Excluded from calculations
- Marked explicitly as missing
- Handled using proportional weight adjustment

---

## Component 1: Supplier Performance Scoring

### Methodology

**Approach:** Weighted Composite Scoring

**Why Unsupervised?**
- No ground-truth supplier performance labels exist
- Cannot invent labels without domain expertise
- Composite scoring provides explainable, transparent methodology

### Features Used

| Feature | Weight | Description |
|---------|--------|-------------|
| Savings Score | 30% | Cost reduction performance |
| Quality Score | 25% | Low defect rate (inverted) |
| Lead Time Score | 20% | Fast delivery (inverted) |
| Compliance Score | 15% | Regulatory/contractual adherence |
| Data Completeness | 10% | Transparency in reporting |

**Total:** 100%

### Feature Engineering

```python
# Savings (higher is better)
savings_score = avg_savings_percentage

# Lead time (lower is better → invert)
lead_time_score = 100 - avg_lead_time_days

# Quality (lower defect rate is better → invert)
quality_score = 100 - avg_defect_rate

# Compliance (already percentage)
compliance_score = compliance_rate

# Data completeness
data_completeness = (orders_with_delivery + orders_with_defect_data) / (2 * total_orders) * 100
```

### Missing Value Handling

If a supplier has missing quality data:
1. Calculate weighted score from available features
2. Adjust weights proportionally (redistribute missing feature's weight)
3. Scale final score back to 0-100 range

**Example:** If quality data is missing (25% weight):
- Remaining features get proportionally more weight
- Total adjusted weight = 75%
- Final score = (weighted_sum / 0.75) * 100

### Performance Categories

| Category | Criteria |
|----------|----------|
| Excellent | Score ≥ 80th percentile |
| Good | Score ≥ 50th percentile |
| Average | Score ≥ 20th percentile |
| Poor | Score < 20th percentile |

### Output Schema

```python
{
    'supplier_id': int,
    'supplier': str,
    'supplier_score': float,      # 0-100
    'supplier_rank': int,          # 1 = best
    'performance_category': str,   # Excellent/Good/Average/Poor
    'total_orders': int,
    'total_cost': float,
    'total_savings': float,
    'avg_savings_percentage': float,
    'avg_lead_time_days': float,
    'avg_defect_rate': float,
    'compliance_rate': float,
    'data_completeness_pct': float
}
```

---

## Component 2: Price Anomaly Detection

### Methodology

**Algorithm:** Isolation Forest

**Why Isolation Forest?**
- Works well with multivariate data
- No distribution assumptions required
- Naturally identifies outliers
- Handles non-linear patterns
- Efficient for large datasets

### Parameters

```python
contamination = 0.05  # Expect ~5% anomalies
n_estimators = 100
max_samples = 'auto'
random_state = 42
```

### Features Used

| Feature | Description |
|---------|-------------|
| `negotiated_price` | Actual price paid |
| `discount_pct` | Discount percentage |
| `order_value` | Total order value |
| `price_deviation_from_avg` | % deviation from supplier-category avg |
| `log_quantity` | Log-transformed quantity |
| `price_deviation_from_rolling` | % deviation from rolling window avg |

### Data Leakage Prevention

**Problem:** Using current record's price to calculate its own "expected" price causes leakage.

**Solution:**
- Historical averages: Calculated from all records in same supplier-category
- Rolling averages: Window-based, naturally excludes future data
- Category patterns: Group-level statistics provide context

### Anomaly Classification

| Anomaly Status | Anomaly Score | Price Level |
|----------------|---------------|-------------|
| Normal | > threshold | Normal |
| Anomaly | < threshold | High (if deviation > 0) |
| Anomaly | < threshold | Low (if deviation < 0) |

### Output Schema

```python
{
    'po_id': str,
    'supplier': str,
    'item_category': str,
    'order_date': date,
    'quantity': int,
    'unit_price': float,
    'negotiated_price': float,
    'total_cost': float,
    'savings_percentage': float,
    'anomaly_score': float,        # More negative = more anomalous
    'anomaly_status': str,         # Normal or Anomaly
    'price_level': str             # High, Low, Normal, Unknown
}
```

---

## Component 3: Demand Forecasting

### Methodology

**Algorithm:** Exponential Smoothing (Holt-Winters)

**Why Exponential Smoothing?**
- Only 2 years of historical data (limited)
- Captures trend and seasonality effectively
- More robust than ARIMA for short series
- Provides prediction intervals
- Computationally efficient

### Aggregation Level

**Monthly Time Series:**
- Overall: Total procurement quantity per month
- By Category: Quantity per category per month

**Why Monthly?**
- Sufficient data points (24 months)
- Appropriate for procurement planning
- Captures seasonal patterns

### Train/Test Split

**CRITICAL: Time-Based Split Only**

```python
# CORRECT: Time-based
train = data[:21 months]  # First 21 months
test = data[21:24 months]  # Last 3 months

# WRONG: Random shuffle would break temporal structure
```

**Why Time-Based?**
- Respects temporal ordering
- Simulates real-world prediction scenario
- Prevents future information leakage

### Model Parameters

```python
trend = 'add'           # Additive trend
seasonal = 'add'        # Additive seasonality
seasonal_periods = 12   # Monthly data
```

**Fallback:** If insufficient data for seasonal model, uses simple exponential smoothing with trend only.

### Evaluation Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| MAE | `mean(abs(actual - predicted))` | Average absolute error |
| RMSE | `sqrt(mean((actual - predicted)²))` | Root mean squared error |
| MAPE | `mean(abs((actual - predicted) / actual)) * 100` | Mean absolute % error |

**Note:** MAPE not calculated if zero values exist (division by zero).

### Forecast Output

```python
{
    'forecast_date': date,         # Future month
    'category': str,               # Category or "Overall"
    'predicted_quantity': int,     # Forecasted demand
    'lower_bound': int,            # 95% CI lower bound
    'upper_bound': int,            # 95% CI upper bound
    'model': str                   # Model type used
}
```

---

## Database Storage

### Tables Created

#### 1. `ml_supplier_scores`
- Stores supplier performance scores
- Primary key: `score_id`
- Foreign key: `supplier_id` → `suppliers`
- Tracks scoring history by `scoring_date`

#### 2. `ml_price_anomalies`
- Stores detected price anomalies
- Primary key: `anomaly_id`
- Foreign keys: `po_id`, `supplier_id`, `category_id`
- Tracks detection history by `detection_date`

#### 3. `ml_demand_forecasts`
- Stores demand predictions
- Primary key: `forecast_id`
- Unique constraint: (`forecast_date`, `category`, `forecast_created_at`)
- Tracks forecast versions by `forecast_created_at`

### Views Created

- `vw_latest_supplier_scores` - Most recent scores
- `vw_active_anomalies` - Current anomalies only
- `vw_latest_forecasts` - Most recent forecasts

---

## Running the Pipeline

### Complete Pipeline

```bash
# Run complete ML pipeline
python -m ml.pipeline

# Skip database save (CSV only)
python -m ml.pipeline --no-db
```

### Individual Components

```python
from ml.pipeline import MLPipeline

pipeline = MLPipeline()

# Run individual components
supplier_results = pipeline.run_supplier_scoring_only()
anomaly_results = pipeline.run_anomaly_detection_only()
forecast_results = pipeline.run_forecasting_only()

# Run complete pipeline
summary = pipeline.run_complete_pipeline(save_to_db=True)
```

### Pipeline Stages

1. **Data Loading:** Load from PostgreSQL
2. **Schema Setup:** Create ML tables
3. **Supplier Scoring:** Score all suppliers
4. **Anomaly Detection:** Detect price anomalies
5. **Demand Forecasting:** Generate forecasts
6. **Evaluation:** Validate all results
7. **Storage:** Save to CSV and PostgreSQL
8. **Reporting:** Generate summary and evaluation reports

---

## Output Files

### Generated Outputs

Located in `ml/outputs/`:

```
supplier_scores_YYYYMMDD_HHMMSS.csv
price_anomalies_YYYYMMDD_HHMMSS.csv
demand_forecasts_YYYYMMDD_HHMMSS.csv
evaluation_report_YYYYMMDD_HHMMSS.json
pipeline_summary_YYYYMMDD_HHMMSS.json
```

### Summary Format

```json
{
  "pipeline_status": "SUCCESS",
  "duration_seconds": 45.23,
  "results_summary": {
    "suppliers_scored": 5,
    "top_supplier": "Epsilon_Group",
    "anomalies_detected": 39,
    "anomaly_percentage": 5.02,
    "forecasts_generated": 18,
    "forecast_mae": 3456.78
  },
  "evaluation_summary": {
    "total_components": 3,
    "components_passed": 3,
    "overall_status": "PASS"
  }
}
```

---

## Evaluation & Validation

### Supplier Scoring Validation

✅ Score range: 0-100  
✅ Unique ranks (no ties)  
✅ All categories present  
✅ No null scores  

### Anomaly Detection Validation

✅ Anomaly rate: 1-15%  
✅ Score distribution reasonable  
✅ Status values valid  
✅ Price levels classified  

### Forecasting Validation

✅ No negative predictions  
✅ Confidence bounds consistent  
✅ MAE/RMSE reasonable  
✅ Time-based train/test split  

---

## Testing

### Run Tests

```bash
# Run all ML tests
pytest tests/test_ml.py -v

# Run specific test class
pytest tests/test_ml.py::TestSupplierScorer -v

# Run with coverage
pytest tests/test_ml.py --cov=ml --cov-report=html
```

### Test Coverage

- ✅ Data loading
- ✅ Feature preprocessing
- ✅ Supplier scoring logic
- ✅ Anomaly detection
- ✅ Demand forecasting
- ✅ Missing value handling
- ✅ Time series split validation
- ✅ Integration test

---

## Limitations & Assumptions

### Data Limitations

1. **Limited Historical Data:** Only 2 years (24 months)
   - Impact: Forecasting has limited training data
   - Mitigation: Use simple, robust model (Exponential Smoothing)

2. **Missing Values:** 11-17% missing in some fields
   - Impact: Reduced sample size for quality/delivery metrics
   - Mitigation: Proportional weight adjustment, data completeness score

3. **No Ground Truth:** No labeled supplier performance
   - Impact: Cannot use supervised learning
   - Mitigation: Use explainable weighted scoring

### Model Assumptions

1. **Supplier Scoring:**
   - Assumes all features contribute independently
   - Weight selection based on business judgment
   - Categories assume roughly uniform distribution

2. **Anomaly Detection:**
   - Assumes ~5% anomaly rate is appropriate
   - Outliers are anomalies (not necessarily fraud)
   - Features assumed to capture price patterns

3. **Forecasting:**
   - Assumes past patterns continue
   - Seasonal patterns repeat annually
   - No external factors modeled (economy, supply chain disruptions)

---

## Future Enhancements

### Potential Improvements

1. **More Historical Data:**
   - Collect 3-5 years of data for better forecasting
   - Improves seasonal pattern detection

2. **Additional Features:**
   - Supplier location/region
   - Payment terms
   - Contract type
   - Market indices

3. **Advanced Models:**
   - Prophet for forecasting (handles holidays, special events)
   - LSTM for complex temporal patterns
   - Ensemble methods for anomaly detection

4. **Real-Time Updates:**
   - Streaming anomaly detection
   - Online learning for supplier scores
   - Automated retraining schedule

---

## Integration with Module 5

Module 5 (AI Procurement Agent) will consume ML results:

### Available Data for Agent

```python
# Load latest ML results
from ml.ml_storage import MLStorage

storage = MLStorage()

supplier_scores = storage.load_latest_supplier_scores()
anomalies = storage.load_active_anomalies()
forecasts = storage.load_latest_forecasts()
```

### Use Cases

1. **Supplier Recommendations:**
   - Agent recommends top-ranked suppliers
   - Warns about poor performers

2. **Anomaly Alerts:**
   - Agent flags unusual prices
   - Suggests investigation actions

3. **Demand Planning:**
   - Agent provides forecast insights
   - Alerts on capacity issues

---

## References

### Algorithms

- **Isolation Forest:** Liu, Fei Tony, Kai Ming Ting, and Zhi-Hua Zhou. "Isolation forest." ICDM 2008.
- **Exponential Smoothing:** Hyndman, R.J., & Athanasopoulos, G. "Forecasting: principles and practice"

### Libraries

- `scikit-learn` 1.3+: Isolation Forest implementation
- `statsmodels` 0.14+: Exponential Smoothing
- `pandas` 2.0+: Data manipulation
- `numpy` 1.24+: Numerical computing

---

## Support & Troubleshooting

### Common Issues

**Issue:** Pipeline fails with "No module named 'sklearn'"
```bash
pip install scikit-learn
```

**Issue:** Forecasting fails with insufficient data
- Ensure at least 12 months of historical data
- Check for missing values in time series

**Issue:** Database connection error
- Verify PostgreSQL is running
- Check `.env` configuration
- Ensure database `procurement_intelligence` exists

### Logs

Check logs for detailed error information:
```bash
tail -f logs/ml_pipeline.log
```

---

## Summary

Module 4 provides production-ready machine learning capabilities:

✅ **Supplier Scoring:** Ranks suppliers based on multi-dimensional performance  
✅ **Anomaly Detection:** Identifies unusual procurement prices  
✅ **Demand Forecasting:** Predicts future demand with confidence intervals  
✅ **Database Integration:** Persists results for downstream consumption  
✅ **Comprehensive Testing:** Full test suite with data quality validation  
✅ **Evaluation Framework:** Automated validation and reporting  

**Ready for Module 5 Integration**
