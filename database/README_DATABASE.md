# Procurement Intelligence System - Database Documentation

## Module 2: PostgreSQL Database Integration

Complete documentation for the PostgreSQL database setup, schema, and data loading process.

---

## Table of Contents

- [Overview](#overview)
- [Database Schema](#database-schema)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Loading Data](#loading-data)
- [Validation](#validation)
- [Database Operations](#database-operations)
- [Troubleshooting](#troubleshooting)

---

## Overview

The procurement database is a normalized PostgreSQL database designed to store and analyze procurement data. The schema consists of 3 main tables:

- **suppliers** (5 records) - Dimension table
- **item_categories** (5 records) - Dimension table  
- **purchase_orders** (777 records) - Fact table

**Key Features:**
- Normalized structure to reduce redundancy
- Foreign key constraints for referential integrity
- Indexes for query performance
- Views for common analytical queries
- Transaction-based data loading
- Comprehensive validation

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────────┐       ┌─────────────────────┐
│   suppliers     │       │  purchase_orders     │       │  item_categories    │
├─────────────────┤       ├──────────────────────┤       ├─────────────────────┤
│ supplier_id (PK)│◄──────┤ supplier_id (FK)     │──────►│ category_id (PK)    │
│ supplier_name   │       │ category_id (FK)     │       │ category_name       │
│ created_at      │       │ po_id (PK)           │       │ created_at          │
│ updated_at      │       │ order_date           │       │ updated_at          │
└─────────────────┘       │ delivery_date        │       └─────────────────────┘
                          │ order_status         │
                          │ compliance           │
                          │ quantity             │
                          │ unit_price           │
                          │ negotiated_price     │
                          │ defective_units      │
                          │ total_cost           │
                          │ savings              │
                          │ savings_percentage   │
                          │ defect_rate          │
                          │ lead_time_days       │
                          │ order_year           │
                          │ order_month          │
                          │ order_quarter        │
                          │ created_at           │
                          │ updated_at           │
                          └──────────────────────┘
```

### Table Details

#### 1. suppliers
**Purpose:** Stores unique supplier information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| supplier_id | SERIAL | PRIMARY KEY | Auto-generated surrogate key |
| supplier_name | VARCHAR(100) | NOT NULL, UNIQUE | Unique supplier name |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record update timestamp |

**Indexes:**
- Primary key index on `supplier_id`
- Index on `supplier_name`

#### 2. item_categories
**Purpose:** Stores unique item/product category information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| category_id | SERIAL | PRIMARY KEY | Auto-generated surrogate key |
| category_name | VARCHAR(100) | NOT NULL, UNIQUE | Unique category name |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record update timestamp |

**Indexes:**
- Primary key index on `category_id`
- Index on `category_name`

#### 3. purchase_orders
**Purpose:** Main fact table storing all purchase order transactions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| po_id | VARCHAR(20) | PRIMARY KEY | Purchase Order ID from source |
| supplier_id | INTEGER | NOT NULL, FK → suppliers | Foreign key to suppliers |
| category_id | INTEGER | NOT NULL, FK → item_categories | Foreign key to categories |
| order_date | DATE | NOT NULL | Date order was placed |
| delivery_date | DATE | NULL | Date order was/will be delivered |
| order_status | VARCHAR(50) | NOT NULL | Status: Delivered, Pending, etc. |
| compliance | BOOLEAN | NOT NULL | Compliance status |
| quantity | INTEGER | NOT NULL, CHECK > 0 | Number of units ordered |
| unit_price | NUMERIC(12,2) | NOT NULL, CHECK >= 0 | Original unit price |
| negotiated_price | NUMERIC(12,2) | NOT NULL, CHECK >= 0 | Negotiated unit price |
| defective_units | NUMERIC(12,2) | NULL | Number of defective units |
| total_cost | NUMERIC(15,2) | NOT NULL | Calculated: quantity × negotiated_price |
| savings | NUMERIC(15,2) | NOT NULL | Calculated savings from negotiation |
| savings_percentage | NUMERIC(8,4) | NOT NULL | Percentage saved |
| defect_rate | NUMERIC(8,4) | NULL | Percentage of defective units |
| lead_time_days | INTEGER | NULL | Days between order and delivery |
| order_year | INTEGER | NOT NULL | Year from order_date |
| order_month | INTEGER | NOT NULL, CHECK 1-12 | Month from order_date |
| order_quarter | INTEGER | NOT NULL, CHECK 1-4 | Quarter from order_date |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record update timestamp |

**Indexes:**
- Primary key index on `po_id`
- Foreign key indexes on `supplier_id`, `category_id`
- Date indexes on `order_date`, `delivery_date`, `order_year`
- Composite index on `(order_year, order_quarter)`
- Status/compliance indexes
- Composite indexes for analytics: `(supplier_id, order_date)`, `(category_id, order_date)`

### Database Views

#### vw_purchase_orders_detail
Denormalized view with supplier and category names joined for easy querying.

#### vw_supplier_performance
Aggregated performance metrics by supplier including total orders, costs, savings, defect rates, and compliance rates.

#### vw_category_performance
Aggregated performance metrics by item category.

---

## Prerequisites

### System Requirements
- PostgreSQL 12+ installed and running
- Python 3.8+
- Network access to PostgreSQL server

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter
- `python-dotenv>=1.0.0` - Environment variable management
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations

---

## Setup Instructions

### Step 1: Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/)

### Step 2: Create Database User

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create user and database
CREATE USER procurement_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE procurement_intelligence OWNER procurement_user;
GRANT ALL PRIVILEGES ON DATABASE procurement_intelligence TO procurement_user;

# Exit psql
\q
```

### Step 3: Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and set your database credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=procurement_intelligence
DB_USER=procurement_user
DB_PASSWORD=your_secure_password
DB_SSLMODE=prefer
DB_CONNECT_TIMEOUT=10
```

**⚠️ Security:** Never commit `.env` to version control. It's already in `.gitignore`.

### Step 4: Test Database Connection

```bash
python -m database.connection
```

Expected output:
```
✓ Database connection successful
```

### Step 5: Create Database Schema

```bash
psql -U procurement_user -d procurement_intelligence -f database/schema.sql
```

Or using Python:
```python
from database.connection import DatabaseConnection

db = DatabaseConnection()
db.execute_sql_file('database/schema.sql')
```

Verify tables were created:
```bash
psql -U procurement_user -d procurement_intelligence -c "\dt"
```

Expected output:
```
                List of relations
 Schema |       Name        | Type  |      Owner      
--------+-------------------+-------+-----------------
 public | item_categories   | table | procurement_user
 public | purchase_orders   | table | procurement_user
 public | suppliers         | table | procurement_user
```

---

## Loading Data

### Prerequisites
Ensure the processed CSV file exists:
```bash
ls -lh data/processed/procurement_cleaned.csv
```

### Load Data into Database

```bash
python -m database.load_data
```

**What happens during data load:**

1. **Extract unique suppliers** from CSV
2. **Insert suppliers** into `suppliers` table (5 records)
3. **Extract unique categories** from CSV
4. **Insert categories** into `item_categories` table (5 records)
5. **Prepare purchase orders** with foreign key mappings
6. **Batch insert purchase orders** into `purchase_orders` table (777 records)
7. **Commit transaction** or rollback on error

**Expected output:**
```
================================================================================
DATA LOAD SUMMARY
================================================================================
✓ Suppliers inserted: 5
✓ Categories inserted: 5
✓ Purchase orders inserted: 777
✓ Duration: X.XX seconds
✓ No errors encountered
================================================================================
```

**Key Features:**
- ✅ **Repeatable** - Uses `ON CONFLICT DO NOTHING` to avoid duplicates
- ✅ **Transactional** - All-or-nothing loading with automatic rollback on error
- ✅ **Error handling** - Comprehensive logging and error messages
- ✅ **NULL handling** - Properly handles missing delivery dates and defect data
- ✅ **Data type conversion** - Converts dates, booleans, and numeric types

---

## Validation

### Run Database Validation

```bash
python -m database.validate_data
```

**Validation checks:**

1. **Record counts** - CSV vs Database
2. **Total quantities** - Sum of all quantities
3. **Total costs** - Sum of all procurement costs
4. **Total savings** - Sum of all savings
5. **Average metrics** - Savings %, defect rate, lead time
6. **Missing values** - Delivery dates, defective units
7. **Referential integrity** - No orphaned foreign keys
8. **Duplicate checks** - No duplicate PO IDs

**Expected output:**
```
================================================================================
DATABASE VALIDATION REPORT
================================================================================
Validation Status: PASSED
Validation Time: X.XX seconds

--- CSV METRICS ---
Total Records: 777
Total Quantity: 850,551
Total Cost: $45,373,696.39
Total Savings: $3,931,126.47

--- DATABASE METRICS ---
Suppliers in DB: 5
Categories in DB: 5
Purchase Orders in DB: 777
Total Quantity: 850,551
Total Cost: $45,373,696.39
Total Savings: $3,931,126.47

--- METRIC COMPARISONS ---
✓ Total Records: CSV=777, DB=777
✓ Total Quantity: CSV=850551, DB=850551
✓ Total Cost: CSV=45373696.39, DB=45373696.39
✓ Total Savings: CSV=3931126.47, DB=3931126.47

--- REFERENTIAL INTEGRITY ---
✓ Orphaned Supplier References: 0
✓ Orphaned Category References: 0
✓ Duplicate PO IDs: 0

✓ All validation checks passed
================================================================================
```

Validation report is saved to: `logs/validation_report_db_YYYYMMDD_HHMMSS.json`

---

## Database Operations

### Connect to Database

**Using psql:**
```bash
psql -U procurement_user -d procurement_intelligence
```

**Using Python:**
```python
from database.connection import DatabaseConnection

db = DatabaseConnection()
conn = db.get_connection()
cursor = conn.cursor()

# Execute queries
cursor.execute("SELECT COUNT(*) FROM purchase_orders")
print(cursor.fetchone())

cursor.close()
conn.close()
```

### Common Queries

**Total records in each table:**
```sql
SELECT 'suppliers' as table_name, COUNT(*) as records FROM suppliers
UNION ALL
SELECT 'item_categories', COUNT(*) FROM item_categories
UNION ALL
SELECT 'purchase_orders', COUNT(*) FROM purchase_orders;
```

**Supplier performance:**
```sql
SELECT * FROM vw_supplier_performance
ORDER BY total_cost DESC;
```

**Category performance:**
```sql
SELECT * FROM vw_category_performance
ORDER BY total_orders DESC;
```

**Top 10 largest orders:**
```sql
SELECT po_id, supplier_name, category_name, total_cost
FROM vw_purchase_orders_detail
ORDER BY total_cost DESC
LIMIT 10;
```

**Orders with defects:**
```sql
SELECT po_id, supplier_name, quantity, defective_units, defect_rate
FROM vw_purchase_orders_detail
WHERE defect_rate IS NOT NULL
ORDER BY defect_rate DESC
LIMIT 10;
```

**Monthly order trends:**
```sql
SELECT 
    order_year,
    order_month,
    COUNT(*) as total_orders,
    SUM(total_cost) as monthly_cost,
    SUM(savings) as monthly_savings
FROM purchase_orders
GROUP BY order_year, order_month
ORDER BY order_year, order_month;
```

### Backup and Restore

**Backup database:**
```bash
pg_dump -U procurement_user procurement_intelligence > backup_$(date +%Y%m%d).sql
```

**Restore database:**
```bash
psql -U procurement_user procurement_intelligence < backup_20261201.sql
```

### Drop and Recreate

**⚠️ Warning:** This will delete all data!

```sql
DROP DATABASE IF EXISTS procurement_intelligence;
CREATE DATABASE procurement_intelligence;
```

Then re-run schema creation and data loading.

---

## Troubleshooting

### Connection Issues

**Error: `connection refused`**
- Check PostgreSQL is running: `brew services list` or `sudo systemctl status postgresql`
- Verify port 5432 is available: `lsof -i :5432`
- Check `DB_HOST` and `DB_PORT` in `.env`

**Error: `authentication failed`**
- Verify username and password in `.env`
- Check PostgreSQL user exists: `psql -U postgres -c "\du"`

**Error: `database does not exist`**
- Create database: `createdb -U procurement_user procurement_intelligence`

### Data Loading Issues

**Error: `FileNotFoundError: CSV file not found`**
- Run Module 1 ETL first: `python -m etl.pipeline`
- Verify file exists: `ls data/processed/procurement_cleaned.csv`

**Error: `duplicate key value violates unique constraint`**
- Database already contains data
- Either drop and recreate tables, or the script will skip duplicates

**Error: `foreign key constraint violation`**
- Suppliers or categories not loaded properly
- Check dimension tables: `SELECT COUNT(*) FROM suppliers;`

### Validation Issues

**Error: `Validation FAILED - metrics don't match`**
- Check for data corruption during load
- Verify CSV hasn't changed since ETL
- Re-run ETL and reload database

### Performance Issues

**Slow queries:**
- Ensure indexes are created: `\di` in psql
- Run `VACUUM ANALYZE;` to update statistics
- Check query plans: `EXPLAIN ANALYZE SELECT ...`

---

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_HOST` | PostgreSQL server hostname | localhost | No |
| `DB_PORT` | PostgreSQL server port | 5432 | No |
| `DB_NAME` | Database name | procurement_intelligence | No |
| `DB_USER` | Database username | - | **Yes** |
| `DB_PASSWORD` | Database password | - | **Yes** |
| `DB_SSLMODE` | SSL connection mode | prefer | No |
| `DB_CONNECT_TIMEOUT` | Connection timeout (seconds) | 10 | No |

---

## File Reference

```
database/
├── __init__.py              # Package initialization
├── schema.sql               # Database schema definition
├── connection.py            # Database connection management
├── load_data.py             # Data loading script
├── validate_data.py         # Database validation script
└── README_DATABASE.md       # This file
```

---

## Next Steps

After successful database setup and validation:

1. ✅ **Module 1 Complete:** ETL pipeline processing
2. ✅ **Module 2 Complete:** Database integration
3. ⏭️ **Module 3:** Power BI dashboard development
4. ⏭️ **Module 4:** Machine Learning models
5. ⏭️ **Module 5:** AI Agent implementation

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review log files in `logs/` directory
3. Verify environment variables in `.env`
4. Check PostgreSQL logs for server-side errors

---

**Last Updated:** Module 2 Implementation
**Database Version:** PostgreSQL 12+
**Schema Version:** 1.0.0
