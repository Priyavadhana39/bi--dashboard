"""
Page 1: Procurement Overview
High-level KPIs and trend analysis for procurement operations.
"""

import dash
from dash import html, dcc, callback, Input, Output
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
    create_section_header
)
from dashboard.styles.design_system import COLORS, GRID_LAYOUTS, COMPONENT_STYLES, apply_chart_theme

dash.register_page(__name__, path='/', name='Procurement Overview')


def layout():
    """Create the overview page layout."""
    # Load data
    connector = get_data_connector()
    df = connector.get_purchase_orders()
    kpis = connector.get_kpi_summary()
    
    # Format KPI values
    total_cost_str = f"${kpis['total_cost']:,.0f}"
    total_savings_str = f"${kpis['total_savings']:,.0f}"
    total_quantity_str = f"{kpis['total_quantity']:,}"
    total_orders_str = f"{kpis['total_orders']:,}"
    avg_savings_pct_str = f"{kpis['avg_savings_pct']:.2f}%"
    avg_lead_time_str = f"{kpis['avg_lead_time']:.1f} days"
    
    # Create monthly aggregations
    df_monthly = df.groupby([df['order_date'].dt.to_period('M'), 'order_year', 'order_month']).agg({
        'total_cost': 'sum',
        'quantity': 'sum',
        'po_id': 'count'
    }).reset_index()
    df_monthly['month_label'] = df_monthly['order_date'].astype(str)
    
    # Monthly spending trend
    fig_monthly_spending = px.line(
        df_monthly,
        x='month_label',
        y='total_cost',
        title='Monthly Procurement Spending Trend',
        labels={'month_label': 'Month', 'total_cost': 'Total Cost ($)'}
    )
    fig_monthly_spending.update_traces(line_color=COLORS['primary'], line_width=3)
    fig_monthly_spending = apply_chart_theme(fig_monthly_spending)
    fig_monthly_spending.update_layout(hovermode='x unified', yaxis_tickformat='$,.0f')
    
    # Spending by supplier
    supplier_spending = df.groupby('supplier')['total_cost'].sum().reset_index()
    supplier_spending = supplier_spending.sort_values('total_cost', ascending=True)
    
    fig_supplier_spending = px.bar(
        supplier_spending,
        x='total_cost',
        y='supplier',
        orientation='h',
        title='Procurement Spending by Supplier',
        labels={'total_cost': 'Total Cost ($)', 'supplier': 'Supplier'}
    )
    fig_supplier_spending.update_traces(marker_color=COLORS['secondary'])
    fig_supplier_spending = apply_chart_theme(fig_supplier_spending)
    fig_supplier_spending.update_layout(xaxis_tickformat='$,.0f')
    
    # Spending by category
    category_spending = df.groupby('item_category')['total_cost'].sum().reset_index()
    category_spending = category_spending.sort_values('total_cost', ascending=False)
    
    fig_category_spending = px.pie(
        category_spending,
        values='total_cost',
        names='item_category',
        title='Procurement Spending by Category',
        hole=0.4
    )
    fig_category_spending.update_traces(textposition='inside', textinfo='percent+label')
    fig_category_spending = apply_chart_theme(fig_category_spending)
    
    # Order status distribution
    status_dist = df['order_status'].value_counts().reset_index()
    status_dist.columns = ['order_status', 'count']
    
    fig_status = px.pie(
        status_dist,
        values='count',
        names='order_status',
        title='Order Status Distribution'
    )
    fig_status = apply_chart_theme(fig_status)
    
    # Monthly purchase volume
    fig_monthly_volume = px.bar(
        df_monthly,
        x='month_label',
        y='quantity',
        title='Monthly Purchase Volume (Units)',
        labels={'month_label': 'Month', 'quantity': 'Quantity'}
    )
    fig_monthly_volume.update_traces(marker_color=COLORS['warning'])
    fig_monthly_volume = apply_chart_theme(fig_monthly_volume)
    fig_monthly_volume.update_layout(yaxis_tickformat=',')
    
    return html.Div([
        # Page Header
        create_page_header(
            title='Procurement Overview',
            description='High-level KPIs and trend analysis for procurement operations'
        ),
        
        # KPI Section
        create_section_header('Key Performance Indicators', 'Summary of procurement metrics', icon='📊'),
        
        # KPI Cards - Row 1
        html.Div([
            create_kpi_card('Total Procurement Cost', total_cost_str, 
                          subtitle='Total spend across all orders',
                          icon='💰', color_mode='error'),
            create_kpi_card('Total Savings', total_savings_str,
                          subtitle='Cost savings through negotiation',
                          icon='💵', color_mode='success'),
            create_kpi_card('Total Quantity', total_quantity_str,
                          subtitle='Units ordered',
                          icon='📦', color_mode='warning'),
        ], style=GRID_LAYOUTS['3_col']),
        
        # KPI Cards - Row 2
        html.Div([
            create_kpi_card('Purchase Orders', total_orders_str,
                          subtitle=f'{kpis["total_orders"]} orders processed',
                          icon='📋', color_mode='info'),
            create_kpi_card('Average Savings', avg_savings_pct_str,
                          subtitle=f'{kpis["total_orders"]} orders analyzed',
                          icon='📈', color_mode='success'),
            create_kpi_card('Average Lead Time', avg_lead_time_str,
                          subtitle=f'{kpis["orders_with_delivery_date"]} orders tracked',
                          icon='⏱️', color_mode='primary'),
        ], style=GRID_LAYOUTS['3_col']),
        
        # Trends Section
        create_section_header('Spending Trends', 'Analysis of procurement spending patterns', icon='📈'),
        
        # Charts Row 1
        html.Div([
            create_chart_container(fig_monthly_spending),
            create_chart_container(fig_supplier_spending),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Distribution Section
        create_section_header('Category & Status Distribution', 'Breakdown by category and order status', icon='📊'),
        
        # Charts Row 2
        html.Div([
            create_chart_container(fig_category_spending),
            create_chart_container(fig_status),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Volume Section
        create_section_header('Purchase Volume', 'Monthly quantity trends', icon='📦'),
        create_chart_container(fig_monthly_volume),
        
    ], style=COMPONENT_STYLES['page_container'])
