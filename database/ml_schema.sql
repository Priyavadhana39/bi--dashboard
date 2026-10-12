/*
Module 4: Machine Learning Schema
Tables for storing ML model results and predictions.
*/

-- ============================================================================
-- ML Supplier Performance Scores
-- ============================================================================
DROP TABLE IF EXISTS ml_supplier_scores CASCADE;

CREATE TABLE ml_supplier_scores (
    score_id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL,
    supplier_score NUMERIC(8, 2) NOT NULL CHECK (supplier_score >= 0 AND supplier_score <= 100),
    supplier_rank INTEGER NOT NULL CHECK (supplier_rank > 0),
    performance_category VARCHAR(20) NOT NULL CHECK (performance_category IN ('Excellent', 'Good', 'Average', 'Poor')),
    total_orders INTEGER NOT NULL,
    total_cost NUMERIC(15, 2) NOT NULL,
    total_savings NUMERIC(15, 2) NOT NULL,
    avg_savings_percentage NUMERIC(8, 4),
    avg_lead_time_days NUMERIC(8, 2),
    avg_defect_rate NUMERIC(8, 4),
    compliance_rate NUMERIC(8, 2),
    data_completeness_pct NUMERIC(8, 2),
    scoring_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50) DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Indexes
CREATE INDEX idx_ml_supplier_scores_supplier ON ml_supplier_scores(supplier_id);
CREATE INDEX idx_ml_supplier_scores_rank ON ml_supplier_scores(supplier_rank);
CREATE INDEX idx_ml_supplier_scores_category ON ml_supplier_scores(performance_category);
CREATE INDEX idx_ml_supplier_scores_date ON ml_supplier_scores(scoring_date);

COMMENT ON TABLE ml_supplier_scores IS 'ML-generated supplier performance scores and rankings';
COMMENT ON COLUMN ml_supplier_scores.supplier_score IS 'Composite performance score (0-100, higher is better)';
COMMENT ON COLUMN ml_supplier_scores.supplier_rank IS 'Rank among all suppliers (1=best)';
COMMENT ON COLUMN ml_supplier_scores.performance_category IS 'Performance category: Excellent, Good, Average, or Poor';
COMMENT ON COLUMN ml_supplier_scores.data_completeness_pct IS 'Percentage of orders with complete delivery and defect data';


-- ============================================================================
-- ML Price Anomalies
-- ============================================================================
DROP TABLE IF EXISTS ml_price_anomalies CASCADE;

CREATE TABLE ml_price_anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    po_id VARCHAR(20) NOT NULL,
    supplier_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    negotiated_price NUMERIC(12, 2) NOT NULL,
    total_cost NUMERIC(15, 2) NOT NULL,
    savings_percentage NUMERIC(8, 4),
    anomaly_score NUMERIC(10, 6) NOT NULL,
    anomaly_status VARCHAR(20) NOT NULL CHECK (anomaly_status IN ('Normal', 'Anomaly')),
    price_level VARCHAR(20) CHECK (price_level IN ('High', 'Low', 'Normal', 'Unknown')),
    detection_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50) DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (category_id) REFERENCES item_categories(category_id)
);

-- Indexes
CREATE INDEX idx_ml_price_anomalies_po ON ml_price_anomalies(po_id);
CREATE INDEX idx_ml_price_anomalies_supplier ON ml_price_anomalies(supplier_id);
CREATE INDEX idx_ml_price_anomalies_category ON ml_price_anomalies(category_id);
CREATE INDEX idx_ml_price_anomalies_status ON ml_price_anomalies(anomaly_status);
CREATE INDEX idx_ml_price_anomalies_price_level ON ml_price_anomalies(price_level);
CREATE INDEX idx_ml_price_anomalies_order_date ON ml_price_anomalies(order_date);

COMMENT ON TABLE ml_price_anomalies IS 'ML-detected price anomalies using Isolation Forest';
COMMENT ON COLUMN ml_price_anomalies.anomaly_score IS 'Anomaly score from model (more negative = more anomalous)';
COMMENT ON COLUMN ml_price_anomalies.anomaly_status IS 'Normal or Anomaly classification';
COMMENT ON COLUMN ml_price_anomalies.price_level IS 'Whether anomaly is High price, Low price, or Unknown';


-- ============================================================================
-- ML Demand Forecasts
-- ============================================================================
DROP TABLE IF EXISTS ml_demand_forecasts CASCADE;

CREATE TABLE ml_demand_forecasts (
    forecast_id SERIAL PRIMARY KEY,
    forecast_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    predicted_quantity INTEGER NOT NULL CHECK (predicted_quantity >= 0),
    lower_bound INTEGER CHECK (lower_bound >= 0),
    upper_bound INTEGER CHECK (upper_bound >= 0),
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) DEFAULT 'v1.0',
    forecast_created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (forecast_date, category, forecast_created_at)
);

-- Indexes
CREATE INDEX idx_ml_demand_forecasts_date ON ml_demand_forecasts(forecast_date);
CREATE INDEX idx_ml_demand_forecasts_category ON ml_demand_forecasts(category);
CREATE INDEX idx_ml_demand_forecasts_created ON ml_demand_forecasts(forecast_created_at);

COMMENT ON TABLE ml_demand_forecasts IS 'ML-generated demand forecasts using Exponential Smoothing';
COMMENT ON COLUMN ml_demand_forecasts.forecast_date IS 'Future date for which demand is predicted';
COMMENT ON COLUMN ml_demand_forecasts.category IS 'Category or "Overall" for aggregate forecast';
COMMENT ON COLUMN ml_demand_forecasts.predicted_quantity IS 'Predicted procurement quantity';
COMMENT ON COLUMN ml_demand_forecasts.lower_bound IS 'Lower bound of 95% confidence interval';
COMMENT ON COLUMN ml_demand_forecasts.upper_bound IS 'Upper bound of 95% confidence interval';


-- ============================================================================
-- Views for Easy Access
-- ============================================================================

-- Latest supplier scores
CREATE OR REPLACE VIEW vw_latest_supplier_scores AS
SELECT 
    s.supplier_name,
    mss.*
FROM ml_supplier_scores mss
JOIN suppliers s ON mss.supplier_id = s.supplier_id
WHERE mss.scoring_date = (SELECT MAX(scoring_date) FROM ml_supplier_scores)
ORDER BY mss.supplier_rank;

COMMENT ON VIEW vw_latest_supplier_scores IS 'Most recent supplier performance scores';


-- Active anomalies
CREATE OR REPLACE VIEW vw_active_anomalies AS
SELECT 
    mpa.anomaly_id,
    mpa.po_id,
    s.supplier_name,
    ic.category_name,
    mpa.order_date,
    mpa.quantity,
    mpa.negotiated_price,
    mpa.total_cost,
    mpa.anomaly_score,
    mpa.anomaly_status,
    mpa.price_level,
    mpa.detection_date
FROM ml_price_anomalies mpa
JOIN suppliers s ON mpa.supplier_id = s.supplier_id
JOIN item_categories ic ON mpa.category_id = ic.category_id
WHERE mpa.anomaly_status = 'Anomaly'
ORDER BY mpa.anomaly_score ASC;

COMMENT ON VIEW vw_active_anomalies IS 'All detected price anomalies';


-- Latest forecasts
CREATE OR REPLACE VIEW vw_latest_forecasts AS
SELECT 
    forecast_date,
    category,
    predicted_quantity,
    lower_bound,
    upper_bound,
    model_type,
    forecast_created_at
FROM ml_demand_forecasts
WHERE forecast_created_at = (SELECT MAX(forecast_created_at) FROM ml_demand_forecasts)
ORDER BY forecast_date, category;

COMMENT ON VIEW vw_latest_forecasts IS 'Most recent demand forecasts';


-- Grant permissions (if needed)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO readwrite_user;
