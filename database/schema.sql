-- ============================================================================
-- Procurement Intelligence System - Database Schema
-- PostgreSQL Database Schema for Procurement Data
-- ============================================================================
-- 
-- This schema is designed based on the processed procurement dataset
-- with 777 purchase orders, 5 suppliers, and 5 item categories.
--
-- Design Principles:
-- 1. Normalized structure to reduce redundancy
-- 2. Appropriate constraints and data types
-- 3. Indexes for performance
-- 4. Foreign key relationships for referential integrity
-- ============================================================================

-- Drop existing tables (in reverse order of dependencies)
DROP TABLE IF EXISTS purchase_orders CASCADE;
DROP TABLE IF EXISTS item_categories CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;

-- ============================================================================
-- DIMENSION TABLE: Suppliers
-- ============================================================================
-- Stores unique supplier information
-- Primary Key: supplier_id (auto-generated)
-- Natural Key: supplier_name (unique business identifier)
-- ============================================================================

CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on supplier_name for lookups
CREATE INDEX idx_suppliers_name ON suppliers(supplier_name);

COMMENT ON TABLE suppliers IS 'Dimension table storing unique supplier information';
COMMENT ON COLUMN suppliers.supplier_id IS 'Auto-generated surrogate key';
COMMENT ON COLUMN suppliers.supplier_name IS 'Unique supplier name from source data';

-- ============================================================================
-- DIMENSION TABLE: Item Categories
-- ============================================================================
-- Stores unique item/product category information
-- Primary Key: category_id (auto-generated)
-- Natural Key: category_name (unique business identifier)
-- ============================================================================

CREATE TABLE item_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on category_name for lookups
CREATE INDEX idx_categories_name ON item_categories(category_name);

COMMENT ON TABLE item_categories IS 'Dimension table storing unique item category information';
COMMENT ON COLUMN item_categories.category_id IS 'Auto-generated surrogate key';
COMMENT ON COLUMN item_categories.category_name IS 'Unique category name from source data';

-- ============================================================================
-- FACT TABLE: Purchase Orders
-- ============================================================================
-- Main fact table storing all purchase order transactions
-- Primary Key: po_id (from source data)
-- Foreign Keys: supplier_id, category_id
-- ============================================================================

CREATE TABLE purchase_orders (
    -- Primary Key
    po_id VARCHAR(20) PRIMARY KEY,
    
    -- Foreign Keys
    supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    category_id INTEGER NOT NULL REFERENCES item_categories(category_id),
    
    -- Order Dates
    order_date DATE NOT NULL,
    delivery_date DATE,  -- Nullable: 87 orders have no delivery date
    
    -- Order Details
    order_status VARCHAR(50) NOT NULL,
    compliance BOOLEAN NOT NULL,
    
    -- Quantities and Pricing
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    negotiated_price NUMERIC(12, 2) NOT NULL CHECK (negotiated_price >= 0),
    
    -- Quality Metrics
    defective_units NUMERIC(12, 2),  -- Nullable: 136 orders have no defect data
    
    -- Calculated Financial Metrics
    total_cost NUMERIC(15, 2) NOT NULL,
    savings NUMERIC(15, 2) NOT NULL,
    savings_percentage NUMERIC(8, 4) NOT NULL,
    
    -- Calculated Quality Metrics
    defect_rate NUMERIC(8, 4),  -- Nullable: only when defective_units exists
    
    -- Calculated Time Metrics
    lead_time_days INTEGER,  -- Nullable: only when delivery_date exists
    
    -- Time Dimensions (for reporting)
    order_year INTEGER NOT NULL,
    order_month INTEGER NOT NULL CHECK (order_month BETWEEN 1 AND 12),
    order_quarter INTEGER NOT NULL CHECK (order_quarter BETWEEN 1 AND 4),
    
    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES for Purchase Orders
-- ============================================================================
-- Indexes to optimize common query patterns

-- Foreign key indexes
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_po_category ON purchase_orders(category_id);

-- Date indexes for time-based queries
CREATE INDEX idx_po_order_date ON purchase_orders(order_date);
CREATE INDEX idx_po_delivery_date ON purchase_orders(delivery_date);
CREATE INDEX idx_po_order_year ON purchase_orders(order_year);
CREATE INDEX idx_po_order_quarter ON purchase_orders(order_year, order_quarter);

-- Status index for filtering
CREATE INDEX idx_po_order_status ON purchase_orders(order_status);

-- Compliance index for filtering
CREATE INDEX idx_po_compliance ON purchase_orders(compliance);

-- Composite index for common analytics queries
CREATE INDEX idx_po_supplier_date ON purchase_orders(supplier_id, order_date);
CREATE INDEX idx_po_category_date ON purchase_orders(category_id, order_date);

-- ============================================================================
-- COMMENTS on Purchase Orders
-- ============================================================================

COMMENT ON TABLE purchase_orders IS 'Fact table storing all purchase order transactions with metrics';
COMMENT ON COLUMN purchase_orders.po_id IS 'Purchase Order ID - unique identifier from source system';
COMMENT ON COLUMN purchase_orders.supplier_id IS 'Foreign key to suppliers table';
COMMENT ON COLUMN purchase_orders.category_id IS 'Foreign key to item_categories table';
COMMENT ON COLUMN purchase_orders.order_date IS 'Date when the purchase order was placed';
COMMENT ON COLUMN purchase_orders.delivery_date IS 'Date when order was/will be delivered (nullable for pending orders)';
COMMENT ON COLUMN purchase_orders.order_status IS 'Current status: Delivered, Pending, Partially Delivered, or Cancelled';
COMMENT ON COLUMN purchase_orders.compliance IS 'Whether the order meets compliance requirements';
COMMENT ON COLUMN purchase_orders.quantity IS 'Number of units ordered';
COMMENT ON COLUMN purchase_orders.unit_price IS 'Original unit price before negotiation';
COMMENT ON COLUMN purchase_orders.negotiated_price IS 'Final negotiated unit price';
COMMENT ON COLUMN purchase_orders.defective_units IS 'Number of defective units (nullable)';
COMMENT ON COLUMN purchase_orders.total_cost IS 'Total order cost = quantity × negotiated_price';
COMMENT ON COLUMN purchase_orders.savings IS 'Total savings from negotiation = (unit_price - negotiated_price) × quantity';
COMMENT ON COLUMN purchase_orders.savings_percentage IS 'Percentage saved through negotiation';
COMMENT ON COLUMN purchase_orders.defect_rate IS 'Percentage of defective units (nullable)';
COMMENT ON COLUMN purchase_orders.lead_time_days IS 'Days between order and delivery (nullable)';

-- ============================================================================
-- CONSTRAINTS Summary
-- ============================================================================
-- Primary Keys: 3 (one per table)
-- Foreign Keys: 2 (purchase_orders -> suppliers, item_categories)
-- Unique Constraints: 2 (supplier_name, category_name)
-- Check Constraints: 5 (quantity > 0, prices >= 0, month/quarter ranges)
-- NOT NULL Constraints: Applied to all required fields
-- ============================================================================

-- ============================================================================
-- DATABASE VIEWS (Optional - for common queries)
-- ============================================================================

-- View: Purchase Orders with Supplier and Category Names
CREATE OR REPLACE VIEW vw_purchase_orders_detail AS
SELECT 
    po.po_id,
    s.supplier_name,
    ic.category_name,
    po.order_date,
    po.delivery_date,
    po.order_status,
    po.compliance,
    po.quantity,
    po.unit_price,
    po.negotiated_price,
    po.defective_units,
    po.total_cost,
    po.savings,
    po.savings_percentage,
    po.defect_rate,
    po.lead_time_days,
    po.order_year,
    po.order_month,
    po.order_quarter
FROM purchase_orders po
JOIN suppliers s ON po.supplier_id = s.supplier_id
JOIN item_categories ic ON po.category_id = ic.category_id;

COMMENT ON VIEW vw_purchase_orders_detail IS 'Denormalized view of purchase orders with supplier and category names';

-- View: Supplier Performance Summary
CREATE OR REPLACE VIEW vw_supplier_performance AS
SELECT 
    s.supplier_name,
    COUNT(*) as total_orders,
    SUM(po.quantity) as total_quantity,
    SUM(po.total_cost) as total_cost,
    SUM(po.savings) as total_savings,
    AVG(po.savings_percentage) as avg_savings_pct,
    AVG(po.defect_rate) as avg_defect_rate,
    AVG(po.lead_time_days) as avg_lead_time_days,
    SUM(CASE WHEN po.compliance = true THEN 1 ELSE 0 END) as compliant_orders,
    ROUND(100.0 * SUM(CASE WHEN po.compliance = true THEN 1 ELSE 0 END) / COUNT(*), 2) as compliance_rate
FROM purchase_orders po
JOIN suppliers s ON po.supplier_id = s.supplier_id
GROUP BY s.supplier_name;

COMMENT ON VIEW vw_supplier_performance IS 'Aggregated performance metrics by supplier';

-- View: Category Performance Summary
CREATE OR REPLACE VIEW vw_category_performance AS
SELECT 
    ic.category_name,
    COUNT(*) as total_orders,
    SUM(po.quantity) as total_quantity,
    SUM(po.total_cost) as total_cost,
    SUM(po.savings) as total_savings,
    AVG(po.savings_percentage) as avg_savings_pct,
    AVG(po.defect_rate) as avg_defect_rate
FROM purchase_orders po
JOIN item_categories ic ON po.category_id = ic.category_id
GROUP BY ic.category_name;

COMMENT ON VIEW vw_category_performance IS 'Aggregated performance metrics by item category';

-- ============================================================================
-- GRANT STATEMENTS (Adjust based on your user roles)
-- ============================================================================
-- Uncomment and modify based on your database user setup
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO procurement_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO procurement_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO procurement_readonly;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
