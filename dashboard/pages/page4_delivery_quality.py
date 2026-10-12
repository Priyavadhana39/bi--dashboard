"""
Page 4: Delivery and Quality Analysis
Analysis of delivery performance, lead times, defects, and compliance.
"""

import dash
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.data_connector import get_data_connector
from dashboard.components.ui_components import (
    create_kpi_card, create_page_header, create_chart_container,
    create_section_header, create_alert
)
from dashboard.styles.design_system import COLORS, GRID_LAYOUTS, COMPONENT_STYLES, apply_chart_theme

dash.register_page(__name__, path='/delivery-quality-analysis', name='Delivery & Quality')


def layout():
    """Create the delivery and quality analysis page layout."""
    # Load data
    connector = get_data_connector()
    df = connector.get_purchase_orders()
    
    # Filter data
    df_with_lead_time = df[df['lead_time_days'].notna()].copy()
    df_with_defects = df[df['defective_units'].notna()].copy()
    
    # Summary metrics
    total_orders = len(df)
    orders_with_delivery = df['delivery_date'].notna().sum()
    orders_with_defects = df['defective_units'].notna().sum()
    avg_lead_time = df_with_lead_time['lead_time_days'].mean()
    avg_defect_rate = df_with_defects['defect_rate'].mean()
    compliant_orders = df['compliance'].sum()
    compliance_rate = (compliant_orders / total_orders) * 100
    
    # Charts with modern theme
    # 1. Lead Time by Supplier
    lead_time_by_supplier = df_with_lead_time.groupby('supplier')['lead_time_days'].mean().reset_index().sort_values('lead_time_days', ascending=True)
    fig_lead_supplier = px.bar(lead_time_by_supplier, x='lead_time_days', y='supplier', orientation='h',
                               title=f'Average Lead Time by Supplier')
    fig_lead_supplier.update_traces(marker_color='#14b8a6')
    fig_lead_supplier = apply_chart_theme(fig_lead_supplier)
    fig_lead_supplier.update_layout(xaxis_tickformat='.1f', showlegend=False)
    
    # 2. Lead Time by Category
    lead_time_by_category = df_with_lead_time.groupby('item_category')['lead_time_days'].mean().reset_index().sort_values('lead_time_days', ascending=False)
    fig_lead_category = px.bar(lead_time_by_category, x='item_category', y='lead_time_days',
                               title='Average Lead Time by Category')
    fig_lead_category.update_traces(marker_color=COLORS['info'])
    fig_lead_category = apply_chart_theme(fig_lead_category)
    fig_lead_category.update_layout(yaxis_tickformat='.1f', showlegend=False)
    
    # 3. Defective Units by Supplier
    defects_by_supplier = df_with_defects.groupby('supplier')['defective_units'].sum().reset_index().sort_values('defective_units', ascending=False)
    fig_defects_supplier = px.bar(defects_by_supplier, x='supplier', y='defective_units',
                                  title='Total Defective Units by Supplier')
    fig_defects_supplier.update_traces(marker_color=COLORS['error'])
    fig_defects_supplier = apply_chart_theme(fig_defects_supplier)
    fig_defects_supplier.update_layout(yaxis_tickformat=',', showlegend=False)
    
    # 4. Defect Rate by Supplier
    defect_rate_by_supplier = df_with_defects.groupby('supplier')['defect_rate'].mean().reset_index().sort_values('defect_rate', ascending=False)
    fig_defect_rate_supplier = px.bar(defect_rate_by_supplier, x='supplier', y='defect_rate',
                                      title='Average Defect Rate by Supplier (%)')
    fig_defect_rate_supplier.update_traces(marker_color=COLORS['warning'], text=defect_rate_by_supplier['defect_rate'].round(2), textposition='outside')
    fig_defect_rate_supplier = apply_chart_theme(fig_defect_rate_supplier)
    fig_defect_rate_supplier.update_layout(yaxis_tickformat='.2f', showlegend=False)
    
    # 5. Compliance
    compliance_counts = df['compliance'].value_counts().reset_index()
    compliance_counts.columns = ['compliance', 'count']
    compliance_counts['compliance_label'] = compliance_counts['compliance'].map({True: 'Compliant', False: 'Non-Compliant'})
    fig_compliance = px.pie(compliance_counts, values='count', names='compliance_label',
                           title='Compliance Distribution',
                           color='compliance_label',
                           color_discrete_map={'Compliant': COLORS['success'], 'Non-Compliant': COLORS['error']})
    fig_compliance.update_traces(textposition='inside', textinfo='percent+label+value')
    fig_compliance = apply_chart_theme(fig_compliance)
    
    # 6. Order Status
    status_counts = df['order_status'].value_counts().reset_index()
    status_counts.columns = ['order_status', 'count']
    fig_status = px.bar(status_counts, x='order_status', y='count',
                       title='Order Status Distribution')
    fig_status = apply_chart_theme(fig_status)
    fig_status.update_layout(showlegend=False)
    fig_status.update_traces(text=status_counts['count'], textposition='outside')
    
    # 7. Delivery Date Availability
    missing_delivery = pd.DataFrame({
        'category': ['With Delivery Date', 'Missing Delivery Date'],
        'count': [df['delivery_date'].notna().sum(), df['delivery_date'].isna().sum()]
    })
    fig_missing_delivery = px.pie(missing_delivery, values='count', names='category',
                                  title='Delivery Date Availability',
                                  color='category',
                                  color_discrete_map={'With Delivery Date': COLORS['success'], 'Missing Delivery Date': COLORS['warning']})
    fig_missing_delivery.update_traces(textposition='inside', textinfo='percent+label+value')
    fig_missing_delivery = apply_chart_theme(fig_missing_delivery)
    
    # 8. Lead Time Distribution
    fig_lead_dist = px.histogram(df_with_lead_time, x='lead_time_days', nbins=20,
                                 title='Lead Time Distribution')
    fig_lead_dist.update_traces(marker_color=COLORS['primary'])
    fig_lead_dist = apply_chart_theme(fig_lead_dist)
    fig_lead_dist.update_layout(showlegend=False, yaxis_title='Number of Orders')
    
    return html.Div([
        create_page_header('Delivery & Quality Analysis', 'Performance metrics for delivery and quality'),
        
        # KPI Cards
        create_section_header('Key Metrics', 'Summary of delivery and quality indicators', icon='📊'),
        html.Div([
            create_kpi_card('Delivery Data', f"{orders_with_delivery}",
                          subtitle=f'{orders_with_delivery/total_orders*100:.1f}% of orders',
                          icon='📦', color_mode='success'),
            create_kpi_card('Avg Lead Time', f"{avg_lead_time:.1f} days",
                          subtitle=f'From {orders_with_delivery} orders',
                          icon='⏱️', color_mode='info'),
            create_kpi_card('Defect Data', f"{orders_with_defects}",
                          subtitle=f'{orders_with_defects/total_orders*100:.1f}% of orders',
                          icon='⚠️', color_mode='warning'),
            create_kpi_card('Avg Defect Rate', f"{avg_defect_rate:.2f}%",
                          subtitle=f'From {orders_with_defects} orders',
                          icon='🔍', color_mode='error'),
        ], style=GRID_LAYOUTS['4_col']),
        
        create_alert(
            f"Missing delivery data: {df['delivery_date'].isna().sum()} orders ({df['delivery_date'].isna().sum()/total_orders*100:.1f}%) • "
            f"Missing defect data: {df['defective_units'].isna().sum()} orders ({df['defective_units'].isna().sum()/total_orders*100:.1f}%) • "
            "Missing data does NOT mean zero defects",
            alert_type='warning'
        ),
        
        # Lead Time Analysis
        create_section_header('Lead Time Analysis', 'Delivery performance by supplier and category', icon='🚚'),
        html.Div([
            create_chart_container(fig_lead_supplier),
            create_chart_container(fig_lead_category),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Defect Analysis
        create_section_header('Defect Analysis', 'Quality metrics and defect rates', icon='🔍'),
        html.Div([
            create_chart_container(fig_defects_supplier),
            create_chart_container(fig_defect_rate_supplier),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Compliance & Status
        create_section_header('Compliance & Status', 'Order compliance and status tracking', icon='✅'),
        html.Div([
            create_chart_container(fig_compliance),
            create_chart_container(fig_status),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Data Availability
        create_section_header('Data Availability', 'Coverage and distribution analysis', icon='📈'),
        html.Div([
            create_chart_container(fig_missing_delivery),
            create_chart_container(fig_lead_dist),
        ], style=GRID_LAYOUTS['2_col']),
        
    ], style=COMPONENT_STYLES['page_container'])
