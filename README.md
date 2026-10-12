# Procurement Intelligence System

## Module 1: Data Collection and ETL Pipeline

A comprehensive ETL (Extract, Transform, Load) pipeline for processing procurement data from the Kaggle Procurement KPI Analysis Dataset.

---

## Table of Contents

- [Overview](#overview)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [ETL Pipeline Stages](#etl-pipeline-stages)
- [Installation](#installation)
- [Usage](#usage)
- [Data Transformations](#data-transformations)
- [Derived Metrics](#derived-metrics)
- [Validation and Quality Checks](#validation-and-quality-checks)
- [Testing](#testing)
- [Logging](#logging)

---

## Overview

This ETL pipeline processes raw procurement data and prepares it for business intelligence analysis. The pipeline ensures data quality, consistency, and enrichment through systematic extraction, transformation, and validation processes.

**Key Features:**
- Automated data extraction with validation
- Comprehensive data cleaning and standardization
- Derived business metrics calculation
- Data quality validation and reporting
- Preserves raw data integrity
- Detailed logging and error handling
- Comprehensive test coverage

---

## Dataset

### Source
**Kaggle Procurement KPI Analysis Dataset**

### Location
- **Raw Data:** `data/raw/Procurement KPI Analysis Dataset.csv`
- **Processed Data:** `data/processed/procurement_cleaned.csv`

⚠️ **Important:** The raw dataset is NEVER modified. All transformations are applied to a copy, and the cleaned data is saved separately.

### Dataset Specifications
- **Total Records:** 776 procurement orders
- **Date Range:** January 2022 - January 2024
- **Suppliers:** 5 unique suppliers
- **Item Categories:** 5 categories (Office Supplies, MRO, Packaging, Raw Materials, Electronics)
- **Order Statuses:** 4 statuses (Delivered, Pending, Cancelled, Partially Delivered)

### Source Columns

| Column | Type | Description |
|--------|------|-------------|
| `PO_ID` | String | Purchase Order ID (unique identifier) |
| `Supplier` | String | Supplier name |
| `Order_Date` | Date | Date when order was placed |
| `Delivery_Date` | Date | Date when order was/will be delivered (may be missing) |
| `Item_Category` | String | Category of items ordered |
| `Order_Status` | String | Current status of the order |
| `Quantity` | Integer | Number of units ordered |
| `Unit_Price` | Float | Original unit price |
| `Negotiated_Price` | Float | Final negotiated price per unit |
| `Defective_Units` | Float | Number of defective units (may be missing) |
| `Compliance` | String | Compliance status (Yes/No) |

---

## Project Structure

```
procurement-intelligence-system/
├── data/
│   ├── raw/
│   │   └── Procurement KPI Analysis Dataset.csv  # Original dataset (READ-ONLY)
│   └── processed/
│       └── procurement_cleaned.csv                # Cleaned dataset (OUTPUT)
├── etl/
│   ├── __init__.py
│   ├── extract.py          # Data extraction module
│   ├── transform.py        # Data transformation module
│   ├── validate.py         # Data validation and reporting module
│   └── pipeline.py         # ETL orchestration
├── tests/
│   ├── __init__.py
│   └── test_etl.py         # Comprehensive test suite
├── logs/
│   ├── etl_pipeline_*.log           # Pipeline execution logs
│   └── validation_report_*.json     # Validation reports
├── requirements.txt
└── README.md
```

---

## ETL Pipeline Stages

### 1. Extract
**Module:** `etl/extract.py`

- Validates raw data file exists
- Reads CSV data using pandas
- Collects extraction metadata (record count, columns, file size)
- Logs extraction statistics

### 2. Transform
**Module:** `etl/transform.py`

**Column Standardization:**
- Converts column names to snake_case format
- Example: `PO_ID` → `po_id`, `Order_Date` → `order_date`

**Data Cleaning:**
- Removes exact duplicate records
- Converts date columns to proper datetime format
- Converts numeric columns to appropriate types
- Standardizes categorical values (trim whitespace)

**Data Validation:**
- Identifies records with negative quantities
- Identifies records with negative prices
- Identifies records where defective_units > quantity
- Logs all validation issues

**Missing Value Handling:**
- Missing `delivery_date`: Preserved as NaT (Not a Time)
- Missing `defective_units`: Preserved as NaN
- No synthetic data generation

### 3. Validate
**Module:** `etl/validate.py`

Generates comprehensive validation reports including:
- Extraction statistics
- Transformation statistics
- Duplicate and invalid record counts
- Missing value analysis (before/after)
- Data quality metrics
- Business metrics summary
- Date ranges and categorical distributions

### 4. Load
**Module:** `etl/pipeline.py`

- Saves cleaned data to `data/processed/procurement_cleaned.csv`
- Saves validation report to `logs/validation_report_*.json`
- Verifies raw data integrity (ensures original file unchanged)

---

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. **Navigate to project directory:**
```bash
cd procurement-intelligence-system
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

---

## Usage

### Running the ETL Pipeline

**Method 1: Using Python module**
```bash
python -m etl.pipeline
```

**Method 2: Direct execution**
```bash
python etl/pipeline.py
```

### Expected Output

The pipeline will:
1. Extract data from `data/raw/Procurement KPI Analysis Dataset.csv`
2. Apply all transformations and validations
3. Save processed data to `data/processed/procurement_cleaned.csv`
4. Generate logs in `logs/etl_pipeline_*.log`
5. Generate validation report in `logs/validation_report_*.json`
6. Display a summary report in the console

### Output Files

**Processed Data:**
- `data/processed/procurement_cleaned.csv` - Clean, enriched dataset with derived columns

**Logs:**
- `logs/etl_pipeline_YYYYMMDD_HHMMSS.log` - Detailed execution log
- `logs/validation_report_YYYYMMDD_HHMMSS.json` - Structured validation report

---

## Data Transformations

### Column Name Changes

| Original | Transformed |
|----------|-------------|
| `PO_ID` | `po_id` |
| `Supplier` | `supplier` |
| `Order_Date` | `order_date` |
| `Delivery_Date` | `delivery_date` |
| `Item_Category` | `item_category` |
| `Order_Status` | `order_status` |
| `Quantity` | `quantity` |
| `Unit_Price` | `unit_price` |
| `Negotiated_Price` | `negotiated_price` |
| `Defective_Units` | `defective_units` |
| `Compliance` | `compliance` |

### Data Type Conversions

| Column | Original Type | Target Type |
|--------|---------------|-------------|
| `order_date` | String | datetime64 |
| `delivery_date` | String | datetime64 |
| `quantity` | String/Mixed | int64 |
| `unit_price` | String/Mixed | float64 |
| `negotiated_price` | String/Mixed | float64 |
| `defective_units` | String/Mixed | float64 |

---

## Derived Metrics

The ETL pipeline creates the following calculated fields:

### 1. Total Cost
```python
total_cost = quantity × negotiated_price
```
**Purpose:** Total amount paid for the order

### 2. Savings
```python
savings = (unit_price - negotiated_price) × quantity
```
**Purpose:** Total amount saved through negotiation

### 3. Savings Percentage
```python
savings_percentage = (savings / (unit_price × quantity)) × 100
```
**Purpose:** Percentage of cost saved through negotiation

### 4. Defect Rate
```python
defect_rate = (defective_units / quantity) × 100  # when defective_units available
```
**Purpose:** Percentage of defective items in the order
**Note:** Only calculated when `defective_units` is not missing

### 5. Lead Time Days
```python
lead_time_days = delivery_date - order_date  # in days
```
**Purpose:** Number of days between order and delivery
**Note:** Only calculated when `delivery_date` is not missing

### 6. Order Year
```python
order_year = year(order_date)
```
**Purpose:** Year when order was placed

### 7. Order Month
```python
order_month = month(order_date)
```
**Purpose:** Month when order was placed (1-12)

### 8. Order Quarter
```python
order_quarter = quarter(order_date)
```
**Purpose:** Quarter when order was placed (1-4)

---

## Validation and Quality Checks

### Automated Checks

1. **File Validation**
   - Verifies raw data file exists
   - Checks file is readable

2. **Duplicate Detection**
   - Identifies and removes exact duplicate records
   - Logs count of duplicates removed

3. **Data Integrity**
   - Detects negative quantities
   - Detects negative prices
   - Identifies defective_units > quantity

4. **Missing Value Tracking**
   - Tracks missing values before transformation
   - Tracks missing values after transformation
   - Reports on missing value patterns

5. **Type Validation**
   - Ensures dates are valid datetime values
   - Ensures numeric fields contain valid numbers

### Validation Report Contents

The validation report includes:

**Extraction Phase:**
- Source file path and size
- Total records extracted
- Column list

**Transformation Phase:**
- Records before/after transformation
- Duplicate records removed
- Invalid records detected
- Missing value analysis

**Final Dataset:**
- Total records and columns
- Complete column list
- Memory usage

**Data Quality:**
- Date ranges (min/max order dates)
- Unique value counts (suppliers, categories, statuses)
- Categorical distributions

**Business Metrics:**
- Total cost sum, mean, median
- Total savings and average savings
- Average savings percentage
- Average defect rate
- Average lead time
- Total quantity ordered

---

## Testing

### Running Tests

**Run all tests:**
```bash
python -m pytest tests/test_etl.py -v
```

**Or using unittest:**
```bash
python tests/test_etl.py
```

### Test Coverage

The test suite includes tests for:

**Data Extraction:**
- File existence validation
- Data loading
- Metadata collection

**Data Transformation:**
- Column name standardization
- Duplicate removal
- Date conversion
- Numeric conversion
- Categorical standardization

**Derived Calculations:**
- Total cost calculation
- Savings calculation
- Savings percentage calculation
- Defect rate calculation
- Lead time calculation

**Edge Cases:**
- Missing value handling
- Negative value detection
- Invalid date handling
- Division by zero protection

**Validation:**
- Report generation
- Report structure verification
- Metric calculations

---

## Logging

### Log Levels

- **INFO:** Normal pipeline operations, progress updates
- **WARNING:** Data quality issues, missing values, invalid records
- **ERROR:** Critical failures, file not found, data corruption

### Log File Format

```
2024-01-15 10:30:45,123 - etl.extract - INFO - Starting data extraction...
2024-01-15 10:30:45,234 - etl.extract - INFO - Extracted 776 records with 11 columns
2024-01-15 10:30:46,345 - etl.transform - WARNING - Removed 0 duplicate records
2024-01-15 10:30:47,456 - etl.transform - INFO - Created 'total_cost' column
```

### Log Locations

- Console output (real-time)
- `logs/etl_pipeline_YYYYMMDD_HHMMSS.log` (persistent)

---

## Data Quality Assumptions

1. **Raw Data Integrity:**
   - The original CSV file is assumed to be from the Kaggle dataset
   - No modifications have been made to the raw file

2. **Missing Values:**
   - Missing `delivery_date` is acceptable (orders in progress)
   - Missing `defective_units` is acceptable (no defects reported or not yet inspected)

3. **Invalid Values:**
   - Negative quantities are flagged but not removed
   - Negative prices are flagged but not removed
   - Invalid records are logged for review

4. **Duplicates:**
   - Exact duplicates are removed automatically
   - Near-duplicates are not detected

---

## Module 2: Database Integration

### PostgreSQL Database

The procurement data is now integrated into a normalized PostgreSQL database:

**Database Structure:**
- **suppliers** table: 5 unique suppliers
- **item_categories** table: 5 item categories  
- **purchase_orders** table: 777 purchase orders with foreign keys

**Key Features:**
- Normalized schema with referential integrity
- 12 performance indexes
- 3 analytical views
- Transaction-based loading
- Comprehensive validation

**Setup Instructions:**
```bash
# 1. Configure database credentials
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 2. Create database schema
psql -U your_user -d procurement_intelligence -f database/schema.sql

# 3. Load data
python -m database.load_data

# 4. Validate data
python -m database.validate_data
```

**Documentation:** See `database/README_DATABASE.md` for complete database documentation.

---

## Next Steps

✅ **Module 1 Complete:** ETL pipeline processing  
✅ **Module 2 Complete:** PostgreSQL database integration  
⏭️ **Module 3:** Power BI dashboard development  
⏭️ **Module 4:** Machine Learning models for forecasting  
⏭️ **Module 5:** AI Agent for procurement intelligence

The processed dataset at `data/processed/procurement_cleaned.csv` and PostgreSQL database are ready for downstream analytics and modeling.

---

## Troubleshooting

### Common Issues

**Issue:** `FileNotFoundError: Raw data file not found`
- **Solution:** Ensure `data/raw/Procurement KPI Analysis Dataset.csv` exists

**Issue:** `PermissionError: Cannot write to output directory`
- **Solution:** Check write permissions for `data/processed/` directory

**Issue:** `ImportError: No module named 'pandas'`
- **Solution:** Run `pip install -r requirements.txt`

**Issue:** Tests failing with missing modules
- **Solution:** Ensure you're in the project root directory and have installed all dependencies

---

## Technical Specifications

- **Python Version:** 3.8+
- **Key Dependencies:** pandas, numpy
- **Input Format:** CSV
- **Output Format:** CSV, JSON (reports)
- **Character Encoding:** UTF-8
- **Date Format:** ISO 8601 (YYYY-MM-DD)

---

## License

This project is part of the Procurement Intelligence System educational project.

---

## Contact & Support

For questions or issues related to the ETL pipeline, please refer to the log files in the `logs/` directory for detailed execution information.
