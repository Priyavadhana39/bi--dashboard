"""
Page 2: Supplier Analysis
Detailed supplier performance metrics with interactive filtering.
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
    create_page_header, create_chart_container, create_filter_section,
    create_alert, create_section_header
)
from dashboard.styles.design_system import COLORS, GRID_LAYOUTS, COMPONENT_STYLES, apply_chart_theme

dash.register_page(__name__, path='/supplier-analysis', name='Supplier Analysis')


def layout():
    """Create the supplier analysis page layout."""
    # Load data
    connector = get_data_connector()
    df = connector.get_purchase_orders()
    supplier_perf = connector.get_supplier_performance()
    
    # Get unique suppliers for filter
    suppliers = sorted(df['supplier'].unique())
    
    return html.Div([
        # Page Header
        create_page_header(
            title='Supplier Performance Analysis',
            description='Detailed supplier metrics with interactive filtering'
        ),
        
        # Filter Section
        create_filter_section([
            html.Div([
                html.Label('Filter by Supplier:', style={
                    'fontWeight': '600',
                    'fontSize': '14px',
                    'marginRight': '10px',
                    'color': COLORS['text_primary']
                }),
                dcc.Dropdown(
                    id='supplier-filter',
                    options=[{'label': 'All Suppliers', 'value': 'ALL'}] + 
                            [{'label': s, 'value': s} for s in suppliers],
                    value='ALL',
                    style={'width': '300px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center'})
        ]),
        
        # Graphs container
        html.Div(id='supplier-analysis-content'),
        
    ], style=COMPONENT_STYLES['page_container'])


@callback(
    Output('supplier-analysis-content', 'children'),
    Input('supplier-filter', 'value')
)
def update_supplier_analysis(selected_supplier):
    """Update supplier analysis based on filter selection."""
    # Load data
    connector = get_data_connector()
    df = connector.get_purchase_orders()
    
    # Filter data
    if selected_supplier != 'ALL':
        df_filtered = df[df['supplier'] == selected_supplier].copy()
        page_title = f"{selected_supplier}"
    else:
        df_filtered = df.copy()
        page_title = "All Suppliers Comparison"
    
    # Aggregate by supplier
    supplier_agg = df_filtered.groupby('supplier').agg({
        'total_cost': 'sum',
        'savings': 'sum',
        'po_id': 'count',
        'quantity': 'sum',
        'savings_percentage': 'mean',
        'lead_time_days': 'mean',
        'defect_rate': 'mean',
        'compliance': lambda x: (x.sum() / len(x)) * 100
    }).reset_index()
    
    supplier_agg.columns = ['supplier', 'total_cost', 'total_savings', 'order_count', 
                            'total_quantity', 'avg_savings_pct', 'avg_lead_time', 
                            'avg_defect_rate', 'compliance_rate']
    
    supplier_agg = supplier_agg.sort_values('total_cost', ascending=False)
    
    # Apply theme to all charts
    # Chart 1: Procurement Cost
    fig_cost = px.bar(supplier_agg, x='supplier', y='total_cost',
                      title='Procurement Cost by Supplier',
                      labels={'total_cost': 'Total Cost ($)', 'supplier': 'Supplier'})
    fig_cost.update_traces(marker_color=COLORS['error'])
    fig_cost = apply_chart_theme(fig_cost)
    fig_cost.update_layout(yaxis_tickformat='$,.0f', showlegend=False)
    
    # Chart 2: Savings
    fig_savings = px.bar(supplier_agg, x='supplier', y='total_savings',
                        title='Total Savings by Supplier',
                        labels={'total_savings': 'Total Savings ($)', 'supplier': 'Supplier'})
    fig_savings.update_traces(marker_color=COLORS['success'])
    fig_savings = apply_chart_theme(fig_savings)
    fig_savings.update_layout(yaxis_tickformat='$,.0f', showlegend=False)
    
    # Chart 3: Order Count
    fig_orders = px.bar(supplier_agg, x='supplier', y='order_count',
                       title='Order Count by Supplier',
                       labels={'order_count': 'Number of Orders', 'supplier': 'Supplier'})
    fig_orders.update_traces(marker_color=COLORS['info'])
    fig_orders = apply_chart_theme(fig_orders)
    fig_orders.update_layout(showlegend=False)
    
    # Chart 4: Quantity
    fig_quantity = px.bar(supplier_agg, x='supplier', y='total_quantity',
                         title='Total Quantity by Supplier',
                         labels={'total_quantity': 'Total Quantity', 'supplier': 'Supplier'})
    fig_quantity.update_traces(marker_color=COLORS['warning'])
    fig_quantity = apply_chart_theme(fig_quantity)
    fig_quantity.update_layout(yaxis_tickformat=',', showlegend=False)
    
    # Chart 5: Savings Percentage
    fig_savings_pct = px.bar(supplier_agg, x='supplier', y='avg_savings_pct',
                            title='Average Savings Percentage',
                            labels={'avg_savings_pct': 'Avg Savings (%)', 'supplier': 'Supplier'})
    fig_savings_pct.update_traces(marker_color='#8b5cf6', text=supplier_agg['avg_savings_pct'].round(2), textposition='outside')
    fig_savings_pct = apply_chart_theme(fig_savings_pct)
    fig_savings_pct.update_layout(yaxis_tickformat='.2f', showlegend=False)
    
    # Chart 6: Lead Time
    supplier_lead = supplier_agg[supplier_agg['avg_lead_time'].notna()].copy()
    fig_lead_time = px.bar(supplier_lead, x='supplier', y='avg_lead_time',
                          title='Average Lead Time (days)',
                          labels={'avg_lead_time': 'Avg Lead Time (days)', 'supplier': 'Supplier'})
    fig_lead_time.update_traces(marker_color='#14b8a6')
    fig_lead_time = apply_chart_theme(fig_lead_time)
    fig_lead_time.update_layout(yaxis_tickformat='.1f', showlegend=False)
    
    # Chart 7: Defect Rate
    supplier_defect = supplier_agg[supplier_agg['avg_defect_rate'].notna()].copy()
    fig_defect = px.bar(supplier_defect, x='supplier', y='avg_defect_rate',
                       title='Average Defect Rate (%)',
                       labels={'avg_defect_rate': 'Avg Defect Rate (%)', 'supplier': 'Supplier'})
    fig_defect.update_traces(marker_color=COLORS['error'])
    fig_defect = apply_chart_theme(fig_defect)
    fig_defect.update_layout(yaxis_tickformat='.2f', showlegend=False)
    
    # Chart 8: Compliance
    fig_compliance = px.bar(supplier_agg, x='supplier', y='compliance_rate',
                           title='Compliance Rate (%)',
                           labels={'compliance_rate': 'Compliance Rate (%)', 'supplier': 'Supplier'})
    fig_compliance.update_traces(marker_color=COLORS['success'], text=supplier_agg['compliance_rate'].round(1), textposition='outside')
    fig_compliance = apply_chart_theme(fig_compliance)
    fig_compliance.update_layout(yaxis_tickformat='.1f', yaxis_range=[0, 100], showlegend=False)
    
    # Summary statistics
    total_records = len(df_filtered)
    records_with_defect_data = df_filtered['defective_units'].notna().sum()
    records_with_lead_time = df_filtered['lead_time_days'].notna().sum()
    
    # Build layout
    return html.Div([
        create_section_header(page_title, f'Analysis of {total_records} purchase orders', icon='📊'),
        
        create_alert(
            f"Defect data: {records_with_defect_data} orders ({records_with_defect_data/total_records*100:.1f}%) • "
            f"Lead time data: {records_with_lead_time} orders ({records_with_lead_time/total_records*100:.1f}%)",
            alert_type='info'
        ),
        
        # Cost & Savings Section
        create_section_header('Financial Metrics', 'Spending and savings analysis', icon='💰'),
        html.Div([
            create_chart_container(fig_cost),
            create_chart_container(fig_savings),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Volume Section
        create_section_header('Order Volume', 'Order count and quantity metrics', icon='📦'),
        html.Div([
            create_chart_container(fig_orders),
            create_chart_container(fig_quantity),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Performance Section
        create_section_header('Performance Metrics', 'Savings percentage and lead time', icon='📈'),
        html.Div([
            create_chart_container(fig_savings_pct),
            create_chart_container(fig_lead_time),
        ], style=GRID_LAYOUTS['2_col']),
        
        # Quality Section
        create_section_header('Quality & Compliance', 'Defect rates and compliance tracking', icon='✅'),
        html.Div([
            create_chart_container(fig_defect),
            create_chart_container(fig_compliance),
        ], style=GRID_LAYOUTS['2_col']),
    ])
