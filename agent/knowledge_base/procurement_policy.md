# ⚠️ DEMONSTRATION DOCUMENT - FOR TESTING ONLY ⚠️

**THIS IS NOT AN OFFICIAL ORGANIZATIONAL POLICY**

This document was created as a sample/demonstration document for testing the AI Agent's RAG (Retrieval-Augmented Generation) system. It contains fictional procurement guidelines and should NOT be considered official company policy or authoritative procurement guidance.

**Purpose**: Testing and development of the AI procurement agent  
**Status**: Sample/Mock Document  
**Authority**: None - This is test data only

---

# Procurement Policy and Guidelines

## Document Version
Version: 1.0  
Last Updated: 2024-01-01  
Status: **SAMPLE DOCUMENT FOR TESTING**

---

## 1. Supplier Evaluation Criteria

### 1.1 Performance Metrics

All suppliers are evaluated based on the following criteria:

- **Savings Percentage**: Discount negotiated from unit price (target: >7%)
- **Lead Time**: Average days from order to delivery (target: <12 days)
- **Quality**: Defect rate percentage (target: <5%)
- **Compliance**: Percentage of orders meeting regulatory requirements (target: >90%)
- **Data Completeness**: Percentage of orders with complete delivery and quality data

### 1.2 Performance Categories

Suppliers are classified into performance tiers:

- **Excellent** (Score >75): Preferred suppliers for critical categories
- **Good** (Score 50-75): Approved for most categories
- **Average** (Score 25-50): Acceptable with monitoring
- **Poor** (Score <25): Requires immediate review and potential replacement

### 1.3 Minimum Requirements

All suppliers must meet these minimum standards:

- Compliance rate >60%
- Defect rate <20%
- No unresolved quality issues

---

## 2. Price Anomaly Investigation

### 2.1 When to Investigate

Price anomalies detected by the ML system should be investigated when:

- Anomaly score < -0.6 (high severity)
- Multiple anomalies from same supplier within 30 days
- High-value orders (>$10,000) flagged as anomalous
- Price significantly deviates from category average

### 2.2 Investigation Process

1. **Review Order Details**: Check PO ID, category, quantity, prices
2. **Compare Historical Prices**: Review price history for supplier/category
3. **Verify Business Justification**: Contact procurement officer
4. **Document Findings**: Record investigation results
5. **Take Action**: Approve, renegotiate, or escalate

### 2.3 Response Actions

- **Minor deviation (<15%)**: Monitor and document
- **Moderate deviation (15-30%)**: Require written justification
- **Major deviation (>30%)**: Mandatory review by senior procurement

---

## 3. Supplier Selection Process

### 3.1 Category-Based Selection

When selecting suppliers for a category:

1. **Review ML Performance Scores**: Check supplier rankings
2. **Analyze Historical Performance**: Review past orders and metrics
3. **Consider Category Expertise**: Evaluate supplier's category experience
4. **Check Anomaly History**: Review price anomaly patterns
5. **Verify Compliance Status**: Ensure regulatory requirements met

### 3.2 Selection Criteria Priority

For critical categories (Electronics, Raw Materials):
1. Quality (40%)
2. Compliance (30%)
3. Lead Time (20%)
4. Savings (10%)

For non-critical categories (Office Supplies, MRO):
1. Savings (35%)
2. Lead Time (30%)
3. Quality (20%)
4. Compliance (15%)

### 3.3 Switching Suppliers

Before switching suppliers:

- Current supplier must have performance category "Poor" OR
- New supplier must score 20+ points higher AND
- New supplier must have minimum 10 historical orders

---

## 4. Demand Forecasting Usage

### 4.1 Forecast Interpretation

Demand forecasts are provided with confidence intervals:

- **Lower Bound**: Minimum expected quantity
- **Predicted**: Most likely quantity
- **Upper Bound**: Maximum expected quantity

### 4.2 Planning Guidelines

- Use **predicted quantity** for capacity planning
- Use **upper bound** for safety stock calculations
- Review forecasts monthly and adjust procurement plans
- Forecasts are estimates, not guarantees

### 4.3 Forecast Limitations

- Based on 24 months historical data
- Does not account for external market changes
- Should be combined with business intelligence
- MAE typically 15-20% of mean demand

---

## 5. Approval Authority

### 5.1 Order Value Thresholds

- **<$5,000**: Procurement officer approval
- **$5,000-$25,000**: Department manager approval
- **$25,000-$100,000**: Senior procurement approval
- **>$100,000**: Executive approval required

### 5.2 Exception Handling

Orders requiring special approval:

- Any order with detected price anomaly
- Supplier performance category "Poor"
- New supplier (no historical orders)
- Non-compliant supplier
- Single-source procurement

---

## 6. Data Quality Standards

### 6.1 Required Data

All purchase orders must include:

- Supplier name and ID
- Item category
- Order date
- Quantity and unit of measure
- Unit price and negotiated price
- Delivery status (when delivered)
- Quality metrics (defect rate when applicable)

### 6.2 Missing Data Handling

- Missing delivery data: Do not assume on-time delivery
- Missing defect data: Do not assume zero defects
- Incomplete data reduces supplier's data completeness score
- Orders with >50% missing data flagged for review

---

## 7. Continuous Improvement

### 7.1 Monthly Reviews

Procurement team must review:

- Supplier performance trends
- Price anomaly patterns
- Forecast accuracy
- Spending by category and supplier

### 7.2 Quarterly Actions

- Re-evaluate poor-performing suppliers
- Update supplier approved list
- Refine ML model parameters (with data science team)
- Review and update procurement policies

---

## Policy Enforcement

This policy is mandatory for all procurement activities. Violations should be reported to the Procurement Manager. Policy exceptions require written approval from executive leadership.

**For questions or clarifications, contact:**  
Procurement Department  
Email: procurement@company.com
