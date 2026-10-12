"""
Procurement Intelligence Dashboard - Main Application
Enterprise-grade multi-page dashboard for procurement analytics, ML insights, and AI-powered analysis.
"""

import sys
import os

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import dash
from dash import Dash, html, dcc
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize the Dash app with pages support
app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title='Procurement Intelligence System'
)

# Modern Enterprise CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                background: #f8fafc;
            }
            
            code {
                font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace;
            }
            
            /* Sidebar Styles */
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                bottom: 0;
                width: 280px;
                background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
                padding: 0;
                box-shadow: 2px 0 12px rgba(0,0,0,0.15);
                overflow-y: auto;
                z-index: 1000;
            }
            
            .sidebar-header {
                padding: 24px 20px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .sidebar-header h2 {
                color: white;
                font-size: 20px;
                font-weight: 700;
                margin: 0;
                line-height: 1.4;
                letter-spacing: -0.5px;
            }
            
            .sidebar-header .subtitle {
                color: rgba(255,255,255,0.7);
                font-size: 13px;
                margin-top: 4px;
            }
            
            .sidebar-nav {
                padding: 16px;
            }
            
            .nav-section-label {
                color: rgba(255,255,255,0.5);
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 12px 16px 8px 16px;
                margin-top: 8px;
            }
            
            .nav-link {
                display: flex;
                align-items: center;
                color: rgba(255,255,255,0.85);
                text-decoration: none;
                padding: 12px 16px;
                margin-bottom: 4px;
                border-radius: 8px;
                transition: all 0.2s ease;
                font-size: 14px;
                font-weight: 500;
            }
            
            .nav-link:hover {
                background: rgba(255,255,255,0.12);
                color: white;
                transform: translateX(4px);
            }
            
            .nav-link.active {
                background: rgba(255,255,255,0.2);
                color: white;
                font-weight: 600;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }
            
            .nav-link .icon {
                margin-right: 12px;
                font-size: 18px;
                width: 24px;
                text-align: center;
            }
            
            .sidebar-footer {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 20px;
                border-top: 1px solid rgba(255,255,255,0.1);
                background: rgba(0,0,0,0.1);
            }
            
            .sidebar-footer p {
                color: rgba(255,255,255,0.5);
                font-size: 11px;
                line-height: 1.6;
                margin: 0;
                text-align: center;
            }
            
            /* Main Content Area */
            .content {
                margin-left: 280px;
                min-height: 100vh;
            }
            
            /* KPI Card Hover Effect */
            .kpi-card:hover {
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                transform: translateY(-2px);
            }
            
            /* Responsive Design */
            @media (max-width: 1024px) {
                .sidebar {
                    width: 240px;
                }
                
                .content {
                    margin-left: 240px;
                }
            }
            
            @media (max-width: 768px) {
                .sidebar {
                    width: 100%;
                    height: auto;
                    position: relative;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
                }
                
                .sidebar-footer {
                    position: relative;
                }
                
                .content {
                    margin-left: 0;
                }
            }
            
            /* Loading Spinner */
            ._dash-loading {
                margin: 40px auto !important;
            }
            
            /* Dropdown Styling */
            .Select-control {
                border-radius: 8px !important;
                border: 2px solid #e2e8f0 !important;
            }
            
            .Select-control:hover {
                border-color: #cbd5e1 !important;
            }
            
            .is-focused .Select-control {
                border-color: #3b82f6 !important;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout with modern sidebar navigation
app.layout = html.Div([
    # Modern Sidebar
    html.Div([
        # Sidebar Header
        html.Div([
            html.H2([
                html.Span('📊 ', style={'fontSize': '24px'}),
                'Procurement Intelligence System'
            ]),
            html.Div('with AI-Powered Supplier Analysis', className='subtitle')
        ], className='sidebar-header'),
        
        # Sidebar Navigation
        html.Div([
            html.Div('ANALYTICS', className='nav-section-label'),
            html.A(
                [html.Span('🏠', className='icon'), 'Procurement Overview'],
                href='/',
                className='nav-link'
            ),
            html.A(
                [html.Span('👥', className='icon'), 'Supplier Analysis'],
                href='/supplier-analysis',
                className='nav-link'
            ),
            html.A(
                [html.Span('💰', className='icon'), 'Price & Spend Analysis'],
                href='/price-spend-analysis',
                className='nav-link'
            ),
            html.A(
                [html.Span('📦', className='icon'), 'Delivery & Quality'],
                href='/delivery-quality-analysis',
                className='nav-link'
            ),
            
            html.Div('AI & ML INSIGHTS', className='nav-section-label'),
            html.A(
                [html.Span('🤖', className='icon'), 'AI Procurement Agent'],
                href='/ai-procurement-agent',
                className='nav-link'
            ),
        ], className='sidebar-nav'),
        
        # Sidebar Footer
        html.Div([
            html.P([
                'Procurement Intelligence System',
                html.Br(),
                'BI Dashboard • ML Analytics • AI Agent',
                html.Br(),
                '© 2024 • Version 2.0'
            ]),
        ], className='sidebar-footer'),
    ], className='sidebar'),
    
    # Main Content Area
    html.Div([
        dash.page_container
    ], className='content'),
])


if __name__ == '__main__':
    try:
        logger.info("Starting Procurement Intelligence Dashboard...")
        logger.info("Dashboard will be available at: http://localhost:8050")
        logger.info("Press Ctrl+C to stop the server")
        
        app.run(
            debug=True,
            host='0.0.0.0',
            port=8050
        )
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}", exc_info=True)
        raise
