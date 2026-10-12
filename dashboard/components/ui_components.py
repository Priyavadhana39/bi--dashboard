"""
Reusable UI Components for Enterprise Dashboard
Consistent component library for all pages
"""

from dash import html, dcc
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.styles.design_system import (
    COLORS, TYPOGRAPHY, SPACING, RADIUS, SHADOWS,
    COMPONENT_STYLES, apply_chart_theme
)


def create_kpi_card(title, value, subtitle=None, trend=None, icon=None, color_mode='primary'):
    """
    Create a professional KPI card component
    
    Args:
        title: KPI title
        value: Main KPI value (string or formatted number)
        subtitle: Optional subtitle text
        trend: Optional trend indicator ('+5%', '-2%', etc.)
        icon: Optional emoji icon
        color_mode: Color theme - 'primary', 'success', 'warning', 'error'
    
    Returns:
        Dash HTML component
    """
    # Determine colors based on mode
    color_map = {
        'primary': COLORS['primary'],
        'success': COLORS['success'],
        'warning': COLORS['warning'],
        'error': COLORS['error'],
        'info': COLORS['info'],
    }
    value_color = color_map.get(color_mode, COLORS['primary'])
    
    # Build card content
    card_content = []
    
    # Icon and title row
    title_row = []
    if icon:
        title_row.append(html.Span(icon, style={'marginRight': SPACING['sm'], 'fontSize': TYPOGRAPHY['font_sizes']['xl']}))
    title_row.append(html.Span(title, style={'fontSize': TYPOGRAPHY['font_sizes']['sm'], 'fontWeight': TYPOGRAPHY['font_weights']['medium']}))
    
    card_content.append(
        html.Div(
            title_row,
            style={
                'color': COLORS['text_secondary'],
                'marginBottom': SPACING['md'],
                'display': 'flex',
                'alignItems': 'center'
            }
        )
    )
    
    # Value
    card_content.append(
        html.H2(
            value,
            style={
                'color': value_color,
                'margin': '0',
                'fontSize': TYPOGRAPHY['font_sizes']['3xl'],
                'fontWeight': TYPOGRAPHY['font_weights']['bold'],
                'lineHeight': TYPOGRAPHY['line_heights']['tight']
            }
        )
    )
    
    # Subtitle and trend row
    if subtitle or trend:
        bottom_row = []
        
        if subtitle:
            bottom_row.append(
                html.Span(
                    subtitle,
                    style={
                        'color': COLORS['text_tertiary'],
                        'fontSize': TYPOGRAPHY['font_sizes']['xs'],
                        'marginRight': SPACING['sm']
                    }
                )
            )
        
        if trend:
            # Determine trend color
            trend_color = COLORS['success'] if '+' in trend else COLORS['error']
            trend_icon = '📈' if '+' in trend else '📉'
            
            bottom_row.append(
                html.Span(
                    f"{trend_icon} {trend}",
                    style={
                        'color': trend_color,
                        'fontSize': TYPOGRAPHY['font_sizes']['xs'],
                        'fontWeight': TYPOGRAPHY['font_weights']['semibold']
                    }
                )
            )
        
        card_content.append(
            html.Div(
                bottom_row,
                style={
                    'marginTop': SPACING['md'],
                    'display': 'flex',
                    'alignItems': 'center'
                }
            )
        )
    
    return html.Div(
        card_content,
        style={
            **COMPONENT_STYLES['kpi_card'],
            'textAlign': 'left',
        },
        className='kpi-card'
    )


def create_section_header(title, description=None, icon=None):
    """
    Create a section header component
    
    Args:
        title: Section title
        description: Optional description text
        icon: Optional emoji icon
    
    Returns:
        Dash HTML component
    """
    header_content = []
    
    # Title with icon
    title_elements = []
    if icon:
        title_elements.append(html.Span(icon, style={'marginRight': SPACING['md']}))
    title_elements.append(html.Span(title))
    
    header_content.append(
        html.H2(
            title_elements,
            style=COMPONENT_STYLES['section_title']
        )
    )
    
    # Description
    if description:
        header_content.append(
            html.P(
                description,
                style={
                    'fontSize': TYPOGRAPHY['font_sizes']['base'],
                    'color': COLORS['text_secondary'],
                    'marginTop': f"-{SPACING['md']}",
                    'marginBottom': SPACING['xl']
                }
            )
        )
    
    return html.Div(header_content)


def create_status_badge(text, status='success'):
    """
    Create a status badge component
    
    Args:
        text: Badge text
        status: Badge status - 'success', 'warning', 'error', 'info'
    
    Returns:
        Dash HTML component
    """
    style_map = {
        'success': COMPONENT_STYLES['status_badge_success'],
        'warning': COMPONENT_STYLES['status_badge_warning'],
        'error': COMPONENT_STYLES['status_badge_error'],
        'info': {
            'backgroundColor': '#dbeafe',
            'color': COLORS['info'],
            'padding': f"{SPACING['xs']} {SPACING['md']}",
            'borderRadius': RADIUS['full'],
            'fontSize': TYPOGRAPHY['font_sizes']['xs'],
            'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
            'display': 'inline-block',
        }
    }
    
    return html.Span(
        text,
        style=style_map.get(status, style_map['info'])
    )


def create_chart_container(figure, title=None, description=None):
    """
    Create a chart container with consistent styling
    
    Args:
        figure: Plotly figure object
        title: Optional chart title (if not in figure)
        description: Optional description text
    
    Returns:
        Dash HTML component
    """
    # Apply theme to figure
    figure = apply_chart_theme(figure)
    
    container_content = []
    
    # Header
    if title or description:
        header = []
        if title:
            header.append(
                html.H3(
                    title,
                    style={
                        'fontSize': TYPOGRAPHY['font_sizes']['lg'],
                        'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
                        'color': COLORS['text_primary'],
                        'marginBottom': SPACING['xs']
                    }
                )
            )
        if description:
            header.append(
                html.P(
                    description,
                    style={
                        'fontSize': TYPOGRAPHY['font_sizes']['sm'],
                        'color': COLORS['text_secondary'],
                        'marginBottom': SPACING['lg']
                    }
                )
            )
        container_content.append(html.Div(header))
    
    # Chart
    container_content.append(
        dcc.Graph(figure=figure, style={'height': '400px'}, config={'displayModeBar': False})
    )
    
    return html.Div(
        container_content,
        style=COMPONENT_STYLES['chart_container']
    )


def create_filter_section(filters):
    """
    Create a filter section with multiple filter controls
    
    Args:
        filters: List of filter components
    
    Returns:
        Dash HTML component
    """
    return html.Div(
        filters,
        style={
            **COMPONENT_STYLES['filter_container'],
            'display': 'flex',
            'gap': SPACING['xl'],
            'flexWrap': 'wrap',
            'alignItems': 'center'
        }
    )


def create_data_table_card(data, title=None):
    """
    Create a styled data table card
    
    Args:
        data: DataFrame or data for table
        title: Optional table title
    
    Returns:
        Dash HTML component
    """
    # This is a placeholder - implement with dash_table when needed
    return html.Div(
        [
            html.H3(title, style=COMPONENT_STYLES['section_title']) if title else None,
            html.Div("Data table placeholder", style={'padding': SPACING['xl']})
        ],
        style=COMPONENT_STYLES['chart_container']
    )


def create_alert(message, alert_type='info', dismissible=False):
    """
    Create an alert/notification component
    
    Args:
        message: Alert message
        alert_type: Alert type - 'success', 'warning', 'error', 'info'
        dismissible: Whether alert can be dismissed
    
    Returns:
        Dash HTML component
    """
    icon_map = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️'
    }
    
    bg_color_map = {
        'success': '#d1fae5',
        'warning': '#fef3c7',
        'error': '#fee2e2',
        'info': '#dbeafe'
    }
    
    border_color_map = {
        'success': '#a7f3d0',
        'warning': '#fbbf24',
        'error': '#fecaca',
        'info': '#93c5fd'
    }
    
    text_color_map = {
        'success': COLORS['success'],
        'warning': COLORS['warning'],
        'error': COLORS['error'],
        'info': COLORS['info']
    }
    
    return html.Div(
        [
            html.Span(icon_map.get(alert_type, ''), style={'fontSize': TYPOGRAPHY['font_sizes']['lg'], 'marginRight': SPACING['md']}),
            html.Span(message, style={'flex': '1'}),
        ],
        style={
            'display': 'flex',
            'alignItems': 'center',
            'padding': SPACING['lg'],
            'backgroundColor': bg_color_map.get(alert_type, bg_color_map['info']),
            'border': f"1px solid {border_color_map.get(alert_type, border_color_map['info'])}",
            'borderRadius': RADIUS['md'],
            'color': text_color_map.get(alert_type, text_color_map['info']),
            'fontSize': TYPOGRAPHY['font_sizes']['sm'],
            'marginBottom': SPACING['xl']
        }
    )


def create_page_header(title, description=None, breadcrumbs=None):
    """
    Create a page header with title and optional breadcrumbs
    
    Args:
        title: Page title
        description: Optional description
        breadcrumbs: Optional list of breadcrumb items
    
    Returns:
        Dash HTML component
    """
    header_content = []
    
    # Breadcrumbs
    if breadcrumbs:
        breadcrumb_items = []
        for i, crumb in enumerate(breadcrumbs):
            if i > 0:
                breadcrumb_items.append(
                    html.Span(' / ', style={'color': COLORS['text_tertiary'], 'margin': f"0 {SPACING['sm']}"})
                )
            breadcrumb_items.append(
                html.Span(
                    crumb,
                    style={
                        'color': COLORS['text_tertiary'] if i < len(breadcrumbs) - 1 else COLORS['text_primary'],
                        'fontSize': TYPOGRAPHY['font_sizes']['sm']
                    }
                )
            )
        
        header_content.append(
            html.Div(
                breadcrumb_items,
                style={'marginBottom': SPACING['md']}
            )
        )
    
    # Title
    header_content.append(
        html.H1(
            title,
            style=COMPONENT_STYLES['page_title']
        )
    )
    
    # Description
    if description:
        header_content.append(
            html.P(
                description,
                style={
                    'fontSize': TYPOGRAPHY['font_sizes']['lg'],
                    'color': COLORS['text_secondary'],
                    'textAlign': 'center',
                    'maxWidth': '800px',
                    'margin': f"{SPACING['md']} auto {SPACING['3xl']} auto"
                }
            )
        )
    
    return html.Div(header_content)


def create_empty_state(title, message, icon='📊', action_button=None):
    """
    Create an empty state component
    
    Args:
        title: Empty state title
        message: Empty state message
        icon: Optional icon
        action_button: Optional action button component
    
    Returns:
        Dash HTML component
    """
    content = [
        html.Div(icon, style={'fontSize': '64px', 'marginBottom': SPACING['xl']}),
        html.H3(title, style={'fontSize': TYPOGRAPHY['font_sizes']['xl'], 'fontWeight': TYPOGRAPHY['font_weights']['semibold'], 'color': COLORS['text_primary'], 'marginBottom': SPACING['md']}),
        html.P(message, style={'fontSize': TYPOGRAPHY['font_sizes']['base'], 'color': COLORS['text_secondary'], 'marginBottom': SPACING['xl']})
    ]
    
    if action_button:
        content.append(action_button)
    
    return html.Div(
        content,
        style={
            'textAlign': 'center',
            'padding': SPACING['5xl'],
            **COMPONENT_STYLES['chart_container']
        }
    )
