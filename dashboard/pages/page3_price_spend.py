"""
Page 3: Price and Spend Analysis
Analysis of pricing, negotiations, and spending patterns.
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
    create_section_header
)
from dashboard.styles.design_system import COLORS, GRID_LAYOUTS, COMPONENT_STYLES, apply_chart_theme

dash.register_page(__name__, path='/price-spend-analysis', name='Price & Spend Analysis')


def layout():
    """Create the price and spend analysis page layout."""
    # Load data
    connector = get_data_connector()
    df = connector.get_purchase_orders()
    
    # Summary metrics
    total_unit_price_value = (df['unit_price'] * df['quantity']).sum()
    total_negotiated_value = df['total_cost'].sum()
    overall_savings = df['savings'].sum()
    overall_savings_pct = (overall_savings / total_unit_price_value) * 100
    
    # Chart 1: Unit Price vs Negotiated Price
    fig_price_comparison = go.Figure()
    fig_price_comparison.add_trace(go.Scatter(
        x=df['unit_price'], y=df['negotiated_price'], mode='markers',
        marker=dict(size=8, color=df['savings_percentage'], colorscale='RdYlGn',
                   showscale=True, colorbar=dict(title="Savings %"), line=dict(width=0.5, color='white')),
        text=df['supplier'],
        hovertemplate='<b>%{text}</b><br>Unit Price: $%{x:.2f}<br>Negotiated Price: $%{y:.2f}<br><extra></extra>'
    ))
    max_price = max(df['unit_price'].max(), df['negotiated_price'].max())
    fig_price_comparison.add_trace(go.Scatter(
        x=[0, max_price], y=[0, max_price], mode='lines',
        line=dict(dash='dash', color=COLORS['error'], width=2),
        name='No Savings Line', showlegend=True
    ))
    fig_price_comparison.update_layout(title='Unit Price vs Negotiated Price',
                                       xaxis_title='Unit Price ($)', yaxis_title='Negotiated Price ($)', height=500)
    fig_price_comparison = apply_chart_theme(fig_price_comparison)
    
    # Chart 2: Savings by Supplier
    savings_by_supplier = df.groupby('supplier')['savings'].sum().reset_index().sort_values('savings', ascending=True)
    fig_savings_supplier = px.bar(savings_by_supplier, x='savings', y='supplier', orientation='h',
                                  title='Total Savings by Supplier')
    fig_savings_supplier.update_traces(marker_color=COLORS['success'])
    fig_savings_supplier = apply_chart_theme(fig_savings_supplier)
    fig_savings_supplier.update_layout(xaxis_tickformat='$,.0f', showlegend=False)
    
    # Chart 3: Savings by Category
    savings_by_category = df.groupby('item_category')['savings'].sum().reset_index().sort_values('savings', ascending=False)
    fig_savings_category = px.bar(savings_by_category, x='item_category', y='savings',
                                  title='Total Savings by Category')
    fig_savings_category.update_traces(marker_color=COLORS['info'])
    fig_savings_category = apply_chart_theme(fig_savings_category)
    fig_savings_category.update_layout(yaxis_tickformat='$,.0f', showlegend=False)
    
    # Chart 4: Monthly Trend
    df_monthly = df.groupby(df['order_date'].dt.to_period('M')).agg({
        'total_cost': 'sum', 'savings': 'sum'
    }).reset_index()
    df_monthly['month'] = df_monthly['order_date'].astype(str)
    
    fig_monthly_trend = go.Figure()
    fig_monthly_trend.add_trace(go.Scatter(x=df_monthly['month'], y=df_monthly['total_cost'],
                                          name='Total Spending', line=dict(color=COLORS['error'], width=3)))
    fig_monthly_trend.add_trace(go.Scatter(x=df_monthly['month'], y=df_monthly['savings'],
                                          name='Total Savings', line=dict(color=COLORS['success'], width=3)))
    fig_monthly_trend.update_layout(title='Monthly Spending and Savings Trend', xaxis_title='Month',
                                   yaxis_title='Amount ($)', yaxis_tickformat='$,.0f',
                                   legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'))
    fig_monthly_trend = apply_chart_theme(fig_monthly_trend)
    
    # Chart 5: Category Cost
    category_cost = df.groupby('item_category')['total_cost'].sum().reset_index().sort_values('total_cost', ascending=False)
    fig_category_cost = px.bar(category_cost, x='item_category', y='total_cost',
                               title='Procurement Cost by Category')
    fig_category_cost.update_traces(marker_color=COLORS['error'])
    fig_category_cost = apply_chart_theme(fig_category_cost)
    fig_category_cost.update_layout(yaxis_tickformat='$,.0f', showlegend=False)
    
    # Chart 6: Volume Distribution
    category_volume = df.groupby('item_category')['quantity'].sum().reset_index().sort_values('quantity', ascending=False)
    fig_category_volume = px.pie(category_volume, values='quantity', names='item_category',
                                 title='Purchase Volume Distribution', hole=0.4)
    fig_category_volume.update_traces(textposition='inside', textinfo='percent+label')
    fig_category_volume = apply_chart_theme(fig_category_volume)
    
    return html.Div([
        create_page_header('Price & Spend Analysis', 'Pricing, negotiations, and spending patterns'),
        
        # KPI Cards
        create_section_header('Financial Summary', 'Cost savings overview', icon='💰'),
        html.Div([
            create_kpi_card('Original Value', f"${total_unit_price_value:,.0f}",
                          subtitle='Based on unit prices', icon='📝', color_mode='error'),
            create_kpi_card('Negotiated Value', f"${total_negotiated_value:,.0f}",
                          subtitle='After negotiation', icon='💵', color_mode='primary'),
            create_kpi_card('Total Savings', f"${overall_savings:,.0f}",
                          subtitle=f'{overall_savings_pct:.2f}% saved', icon='✅', color_mode='success'),
        ], style=GRID_LAYOUTS['3_col']),
        
        # Price Comparison
        create_section_header('Price Negotiation Analysis', 'Unit price vs negotiated price comparison', icon='📊'),
        create_chart_container(fig_price_comparison),
        
        # Savings Analysis
        create_section_header('Savings Breakdown', 'Savings by supplier and category', icon='💵'),
        html.Div([
            create_chart_container(fig_savings_supplier),
            create_chart_container(fig_savings_category),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Trends
        create_section_header('Spending Trends', 'Monthly spending and savings patterns', icon='📈'),
        create_chart_container(fig_monthly_trend),
        
        # Category Analysis
        create_section_header('Category Distribution', 'Cost and volume by category', icon='📦'),
        html.Div([
            create_chart_container(fig_category_cost),
            create_chart_container(fig_category_volume),
        ], style=GRID_LAYOUTS['2_col']),
        
    ], style=COMPONENT_STYLES['page_container'])
