# Procurement Intelligence Dashboard

## Module 3: Business Intelligence Dashboard

Interactive web-based dashboard for procurement analytics and insights using Plotly Dash.

---

## Table of Contents

- [Overview](#overview)
- [Dashboard Pages](#dashboard-pages)
- [Installation](#installation)
- [Running the Dashboard](#running-the-dashboard)
- [Features](#features)
- [Data Sources](#data-sources)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Procurement Intelligence Dashboard is a professional, interactive web-based BI tool that provides comprehensive analytics on procurement operations. It connects directly to the PostgreSQL database and presents data through 4 specialized pages with 27 visualizations total.

**Key Features:**
- 📊 **4 Interactive Pages** with navigation sidebar
- 📈 **27 Visualizations** (charts, graphs, KPI cards)
- 🔍 **Interactive Filtering** on supplier analysis page
- 💾 **Direct PostgreSQL Integration** using validated data
- ⚠️ **Data Availability Awareness** - clearly indicates missing data
- 📱 **Responsive Design** - works on desktop and tablet

---

## Dashboard Pages

### Page 1: Procurement Overview 🏠

**Purpose:** High-level overview of procurement operations

**KPI Cards (6):**
1. Total Procurement Cost
2. Total Savings
3. Total Quantity Ordered
4. Number of Purchase Orders
5. Average Savings Percentage
6. Average Lead Time

**Visualizations (5):**
1. **Monthly Procurement Spending Trend** - Line chart showing spending over time
2. **Procurement Spending by Supplier** - Horizontal bar chart
3. **Procurement Spending by Category** - Pie chart with percentages
4. **Order Status Distribution** - Pie chart (Delivered, Pending, Cancelled, Partially Delivered)
5. **Monthly Purchase Volume** - Bar chart showing units ordered per month

**Use Case:** Executive overview, quick insights into procurement health

---

### Page 2: Supplier Analysis 👥

**Purpose:** Detailed supplier performance comparison

**Interactive Filter:**
- Dropdown to select individual suppliers or view all

**Visualizations (8):**
1. **Supplier-wise Procurement Cost** - Bar chart with color scale
2. **Supplier-wise Total Savings** - Bar chart
3. **Supplier-wise Order Count** - Bar chart
4. **Supplier-wise Total Quantity** - Bar chart
5. **Supplier-wise Average Savings Percentage** - Bar chart with values
6. **Supplier-wise Average Lead Time** - Bar chart (only orders with delivery dates)
7. **Supplier-wise Average Defect Rate** - Bar chart (only orders with defect data)
8. **Supplier Compliance Rate** - Bar chart with percentage values

**Data Availability Note:**
- Shows percentage of orders with delivery date data
- Shows percentage of orders with defect data
- Clearly states that missing data ≠ zero

**Use Case:** Supplier evaluation, vendor selection, performance monitoring

---

### Page 3: Price & Spend Analysis 💰

**Purpose:** Pricing, negotiations, and spending patterns

**Summary Cards (3):**
1. Original Value (Unit Price)
2. Negotiated Value
3. Total Savings (with percentage)

**Visualizations (6):**
1. **Unit Price vs Negotiated Price** - Scatter plot with savings % color coding
   - Points below diagonal = savings achieved
   - Color scale shows savings percentage
2. **Total Savings by Supplier** - Horizontal bar chart
3. **Total Savings by Category** - Bar chart
4. **Monthly Spending and Savings Trend** - Dual-line chart
5. **Category-wise Procurement Cost** - Bar chart
6. **Purchase Volume Distribution by Category** - Donut chart

**Use Case:** Cost analysis, negotiation effectiveness, category spending

---

### Page 4: Delivery & Quality Analysis 📦

**Purpose:** Delivery performance and quality metrics

**Summary Cards (4):**
1. Orders with Delivery Data (count and percentage)
2. Average Lead Time (from orders with delivery dates)
3. Orders with Defect Data (count and percentage)
4. Average Defect Rate (from orders with defect data)

**Visualizations (8):**
1. **Average Lead Time by Supplier** - Horizontal bar chart
2. **Lead Time by Category** - Bar chart
3. **Total Defective Units by Supplier** - Bar chart
4. **Average Defect Rate by Supplier** - Bar chart with percentages
5. **Compliance Distribution** - Pie chart (Compliant vs Non-Compliant)
6. **Order Status Distribution** - Bar chart with counts
7. **Delivery Date Data Availability** - Pie chart showing missing data
8. **Lead Time Distribution** - Histogram showing delivery time patterns

**Important Data Notice:**
A prominent yellow alert box explains:
- 87 orders (11.2%) have no delivery date
- 136 orders (17.5%) have no defect data
- **Missing data does NOT mean zero defects or instant delivery**
- Calculations exclude missing values

**Use Case:** Performance monitoring, quality assessment, delivery tracking

---

## Installation

### Prerequisites

1. **PostgreSQL Database** - Must be running with `procurement_intelligence` database loaded
2. **Python 3.8+** - With pip package manager
3. **Modules 1 & 2 Complete** - ETL pipeline and database integration

### Install Dependencies

```bash
# Navigate to project directory
cd "/Users/priyavadhanam/bi-project /procurement-intelligence-system"

# Install all dependencies
pip install -r requirements.txt
```

**Required packages:**
- `dash>=2.14.0` - Dashboard framework
- `plotly>=5.18.0` - Visualization library
- `pandas>=2.0.0` - Data manipulation
- `psycopg2-binary>=2.9.0` - PostgreSQL connector
- `python-dotenv>=1.0.0` - Environment variables

---

## Running the Dashboard

### Step 1: Ensure Database is Running

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify database exists and has data
psql -U priyavadhanam -d procurement_intelligence -c "SELECT COUNT(*) FROM purchase_orders;"
```

Expected output: `777`

### Step 2: Verify Environment Configuration

Ensure `.env` file is configured with database credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=procurement_intelligence
DB_USER=priyavadhanam
DB_PASSWORD=
```

### Step 3: Start the Dashboard

```bash
# From project root directory
python -m dashboard.app
```

**OR**

```bash
# Navigate to dashboard directory
cd dashboard
python app.py
```

### Step 4: Access the Dashboard

Open your web browser and navigate to:
```
http://localhost:8050
```

**Expected Output:**
```
Starting Procurement Intelligence Dashboard...
Dashboard will be available at: http://localhost:8050
Press Ctrl+C to stop the server
Dash is running on http://0.0.0.0:8050/

 * Serving Flask app 'app'
 * Debug mode: on
```

### Step 5: Navigate the Dashboard

- Click on page links in the sidebar to navigate between pages
- Use the supplier filter on Page 2 to analyze individual suppliers
- Hover over charts for detailed information
- Charts are interactive - zoom, pan, and explore

### Stopping the Dashboard

Press `Ctrl+C` in the terminal where the dashboard is running.

---

## Features

### Interactive Elements

**Navigation:**
- Sidebar navigation with 4 page links
- Clean, modern UI with professional styling
- Mobile-responsive design

**Charts:**
- **Hover** - Show detailed information
- **Zoom** - Click and drag to zoom into charts
- **Pan** - Shift+drag to pan around zoomed charts
- **Reset** - Double-click to reset view

**Filtering:**
- **Supplier Filter** (Page 2) - Dropdown to analyze specific suppliers

### Data Handling

**Missing Data:**
- ✅ Clearly identified in visualizations
- ✅ Excluded from calculations (not treated as zero)
- ✅ Percentage of available data shown
- ✅ Yellow alert boxes explain limitations

**Real-time Updates:**
- Dashboard reads from PostgreSQL database
- Data can be refreshed by reloading the page
- Cached for performance during a session

**Data Validation:**
- Uses validated data from Module 2
- Matches CSV totals exactly:
  - 777 purchase orders
  - $45,373,696.39 total cost
  - $3,931,126.47 total savings

---

## Data Sources

### Primary Data Source
**PostgreSQL Database:** `procurement_intelligence`

**Tables Used:**
- `purchase_orders` - Main fact table (777 records)
- `suppliers` - Supplier dimension (5 records)
- `item_categories` - Category dimension (5 records)

**Views Used:**
- `vw_purchase_orders_detail` - Denormalized view with names
- `vw_supplier_performance` - Aggregated supplier metrics
- `vw_category_performance` - Aggregated category metrics

### Data Connector
**Module:** `dashboard/data_connector.py`

**Methods:**
- `get_purchase_orders()` - Fetches all purchase order details
- `get_supplier_performance()` - Fetches supplier performance metrics
- `get_category_performance()` - Fetches category performance metrics
- `get_kpi_summary()` - Calculates high-level KPIs

**Caching:**
- Data is cached in memory for the session
- Improves page load performance
- Can be cleared with `clear_cache()` method

---

## File Structure

```
dashboard/
├── __init__.py                 # Package initialization
├── app.py                      # Main Dash application
├── data_connector.py           # PostgreSQL data fetcher
├── pages/
│   ├── page1_overview.py       # Page 1: Procurement Overview
│   ├── page2_supplier.py       # Page 2: Supplier Analysis
│   ├── page3_price_spend.py    # Page 3: Price & Spend Analysis
│   └── page4_delivery_quality.py # Page 4: Delivery & Quality
├── assets/                     # (optional) Custom CSS/JS
├── components/                 # (optional) Reusable components
└── README_DASHBOARD.md         # This file
```

---

## Troubleshooting

### Dashboard won't start

**Error:** `ModuleNotFoundError: No module named 'dash'`
- **Solution:** Install dependencies: `pip install -r requirements.txt`

**Error:** `connection refused`
- **Solution:** Ensure PostgreSQL is running and accessible
- Check: `pg_isready -h localhost -p 5432`

**Error:** `relation "purchase_orders" does not exist`
- **Solution:** Run Module 2 database setup first
- See: `database/README_DATABASE.md`

### Charts not loading

**Problem:** Page loads but charts are blank
- **Solution 1:** Check browser console for JavaScript errors
- **Solution 2:** Verify database has data: `SELECT COUNT(*) FROM purchase_orders;`
- **Solution 3:** Check logs: `tail -f logs/dashboard.log`

**Problem:** "No data available" message
- **Solution:** Verify Module 2 data loading completed successfully
- Run: `python -m database.validate_data`

### Performance issues

**Problem:** Dashboard is slow to load
- **Solution 1:** Data is cached after first load - refresh page
- **Solution 2:** Check PostgreSQL performance: `EXPLAIN ANALYZE SELECT * FROM vw_purchase_orders_detail;`
- **Solution 3:** Ensure indexes are created: `\di` in psql

### Port already in use

**Error:** `OSError: [Errno 48] Address already in use`
- **Solution 1:** Stop other process using port 8050
- **Solution 2:** Change port in `app.py`: `app.run_server(port=8051)`
- **Solution 3:** Kill process: `lsof -ti:8050 | xargs kill`

### Browser compatibility

**Tested On:**
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**Not Supported:**
- ❌ Internet Explorer

---

## Technical Specifications

**Framework:** Plotly Dash 2.14+  
**Visualization:** Plotly 5.18+  
**Backend:** Flask (via Dash)  
**Database:** PostgreSQL 12+  
**Python:** 3.8+  

**Performance:**
- Dashboard loads in < 5 seconds on localhost
- Charts render in < 1 second
- Data cached for session duration
- Supports 100+ concurrent users (with proper deployment)

---

## Deployment (Optional)

### Production Deployment

For production deployment, consider:

1. **Use a WSGI server** (Gunicorn, uWSGI)
   ```bash
   pip install gunicorn
   gunicorn dashboard.app:server -b 0.0.0.0:8050
   ```

2. **Set debug=False** in `app.run_server()`

3. **Use environment variables** for configuration

4. **Add authentication** if needed (Dash Enterprise, custom auth)

5. **Set up reverse proxy** (Nginx, Apache)

6. **Enable HTTPS** for secure connections

### Cloud Deployment

**Options:**
- Heroku
- AWS Elastic Beanstalk
- Google App Engine
- Azure App Service
- DigitalOcean App Platform

---

## Academic Use

This dashboard is designed for final-year academic project demonstration:

**Suitable For:**
- ✅ Project presentations
- ✅ Demo to evaluators
- ✅ Screenshots in report
- ✅ Live demo on localhost
- ✅ Thesis/dissertation documentation

**Professional Quality:**
- Clean, modern design
- Interactive and engaging
- Real data from validated database
- Comprehensive analytics
- Production-ready code

---

## Support

**For Issues:**
1. Check this README
2. Review `logs/dashboard.log`
3. Verify database connection
4. Check Python package versions

**Logs Location:**
- Dashboard logs: `logs/dashboard.log`
- Database logs: `logs/data_load.log`
- Validation logs: `logs/data_validation.log`

---

## Next Steps

After Module 3 completion:

✅ **Module 1 Complete:** ETL Pipeline  
✅ **Module 2 Complete:** PostgreSQL Database  
✅ **Module 3 Complete:** BI Dashboard  
⏭️ **Module 4:** Machine Learning Models  
⏭️ **Module 5:** AI Procurement Agent  

The dashboard provides a solid foundation for demonstrating procurement intelligence and can be extended with ML predictions and AI insights in future modules.

---

**Dashboard Version:** 1.0.0  
**Last Updated:** Module 3 Implementation  
**Status:** Production Ready ✅
