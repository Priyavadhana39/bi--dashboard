"""
Enterprise Design System for Procurement Intelligence Dashboard
Centralized styling constants and reusable component styles
"""

# Color Palette
COLORS = {
    # Primary Colors
    'primary': '#1e3a8a',  # Deep blue
    'primary_light': '#3b82f6',
    'primary_dark': '#1e40af',
    
    # Secondary Colors
    'secondary': '#059669',  # Green for success/positive
    'secondary_light': '#10b981',
    
    # Status Colors
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'info': '#3b82f6',
    
    # Neutral Colors
    'text_primary': '#1e293b',
    'text_secondary': '#64748b',
    'text_tertiary': '#94a3b8',
    'text_light': '#cbd5e1',
    
    # Background Colors
    'bg_primary': '#ffffff',
    'bg_secondary': '#f8fafc',
    'bg_tertiary': '#f1f5f9',
    'bg_dark': '#0f172a',
    
    # Border Colors
    'border_light': '#e2e8f0',
    'border_medium': '#cbd5e1',
    'border_dark': '#94a3b8',
}

# Typography
TYPOGRAPHY = {
    'font_family': "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
    'font_sizes': {
        'xs': '12px',
        'sm': '14px',
        'base': '16px',
        'lg': '18px',
        'xl': '20px',
        '2xl': '24px',
        '3xl': '30px',
        '4xl': '36px',
        '5xl': '48px',
    },
    'font_weights': {
        'normal': '400',
        'medium': '500',
        'semibold': '600',
        'bold': '700',
    },
    'line_heights': {
        'tight': '1.25',
        'normal': '1.5',
        'relaxed': '1.75',
    }
}

# Spacing
SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '12px',
    'lg': '16px',
    'xl': '20px',
    '2xl': '24px',
    '3xl': '32px',
    '4xl': '40px',
    '5xl': '48px',
}

# Border Radius
RADIUS = {
    'sm': '4px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    'full': '9999px',
}

# Shadows
SHADOWS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'base': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
}

# Component Styles
COMPONENT_STYLES = {
    'kpi_card': {
        'backgroundColor': COLORS['bg_primary'],
        'padding': SPACING['2xl'],
        'borderRadius': RADIUS['lg'],
        'boxShadow': SHADOWS['md'],
        'border': f"1px solid {COLORS['border_light']}",
        'transition': 'all 0.3s ease',
    },
    
    'kpi_card_hover': {
        'boxShadow': SHADOWS['lg'],
        'transform': 'translateY(-2px)',
    },
    
    'chart_container': {
        'backgroundColor': COLORS['bg_primary'],
        'padding': SPACING['2xl'],
        'borderRadius': RADIUS['lg'],
        'boxShadow': SHADOWS['md'],
        'border': f"1px solid {COLORS['border_light']}",
        'marginBottom': SPACING['xl'],
    },
    
    'filter_container': {
        'backgroundColor': COLORS['bg_primary'],
        'padding': SPACING['xl'],
        'borderRadius': RADIUS['md'],
        'boxShadow': SHADOWS['base'],
        'border': f"1px solid {COLORS['border_light']}",
        'marginBottom': SPACING['xl'],
    },
    
    'button_primary': {
        'backgroundColor': COLORS['primary'],
        'color': COLORS['bg_primary'],
        'border': 'none',
        'padding': f"{SPACING['md']} {SPACING['2xl']}",
        'fontSize': TYPOGRAPHY['font_sizes']['sm'],
        'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
        'borderRadius': RADIUS['md'],
        'cursor': 'pointer',
        'transition': 'all 0.2s ease',
    },
    
    'button_secondary': {
        'backgroundColor': COLORS['bg_tertiary'],
        'color': COLORS['text_primary'],
        'border': f"1px solid {COLORS['border_medium']}",
        'padding': f"{SPACING['md']} {SPACING['2xl']}",
        'fontSize': TYPOGRAPHY['font_sizes']['sm'],
        'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
        'borderRadius': RADIUS['md'],
        'cursor': 'pointer',
        'transition': 'all 0.2s ease',
    },
    
    'input_field': {
        'width': '100%',
        'padding': SPACING['md'],
        'fontSize': TYPOGRAPHY['font_sizes']['sm'],
        'border': f"2px solid {COLORS['border_light']}",
        'borderRadius': RADIUS['md'],
        'fontFamily': TYPOGRAPHY['font_family'],
        'transition': 'border-color 0.2s ease',
    },
    
    'page_container': {
        'padding': SPACING['3xl'],
        'backgroundColor': COLORS['bg_secondary'],
        'minHeight': '100vh',
    },
    
    'page_title': {
        'fontSize': TYPOGRAPHY['font_sizes']['4xl'],
        'fontWeight': TYPOGRAPHY['font_weights']['bold'],
        'color': COLORS['text_primary'],
        'marginBottom': SPACING['3xl'],
        'textAlign': 'center',
    },
    
    'section_title': {
        'fontSize': TYPOGRAPHY['font_sizes']['2xl'],
        'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
        'color': COLORS['text_primary'],
        'marginBottom': SPACING['xl'],
    },
    
    'status_badge_success': {
        'backgroundColor': '#d1fae5',
        'color': COLORS['success'],
        'padding': f"{SPACING['xs']} {SPACING['md']}",
        'borderRadius': RADIUS['full'],
        'fontSize': TYPOGRAPHY['font_sizes']['xs'],
        'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
        'display': 'inline-block',
    },
    
    'status_badge_warning': {
        'backgroundColor': '#fef3c7',
        'color': COLORS['warning'],
        'padding': f"{SPACING['xs']} {SPACING['md']}",
        'borderRadius': RADIUS['full'],
        'fontSize': TYPOGRAPHY['font_sizes']['xs'],
        'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
        'display': 'inline-block',
    },
    
    'status_badge_error': {
        'backgroundColor': '#fee2e2',
        'color': COLORS['error'],
        'padding': f"{SPACING['xs']} {SPACING['md']}",
        'borderRadius': RADIUS['full'],
        'fontSize': TYPOGRAPHY['font_sizes']['xs'],
        'fontWeight': TYPOGRAPHY['font_weights']['semibold'],
        'display': 'inline-block',
    },
}

# Chart Theme
CHART_THEME = {
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    'font': {
        'family': TYPOGRAPHY['font_family'],
        'size': 12,
        'color': COLORS['text_secondary']
    },
    'title': {
        'font': {
            'size': 16,
            'weight': 600,
            'color': COLORS['text_primary']
        }
    },
    'xaxis': {
        'gridcolor': COLORS['border_light'],
        'linecolor': COLORS['border_medium'],
    },
    'yaxis': {
        'gridcolor': COLORS['border_light'],
        'linecolor': COLORS['border_medium'],
    },
    'colorway': [
        COLORS['primary'],
        COLORS['secondary'],
        COLORS['warning'],
        COLORS['info'],
        '#8b5cf6',  # Purple
        '#ec4899',  # Pink
        '#f97316',  # Orange
        '#14b8a6',  # Teal
    ]
}

# Grid Layouts
GRID_LAYOUTS = {
    '2_col': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(2, 1fr)',
        'gap': SPACING['xl'],
        'marginBottom': SPACING['xl'],
    },
    '3_col': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(3, 1fr)',
        'gap': SPACING['xl'],
        'marginBottom': SPACING['xl'],
    },
    '4_col': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(4, 1fr)',
        'gap': SPACING['xl'],
        'marginBottom': SPACING['xl'],
    },
    'responsive_2_col': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(300px, 1fr))',
        'gap': SPACING['xl'],
        'marginBottom': SPACING['xl'],
    }
}


def get_kpi_color(value, thresholds={'high': 80, 'medium': 50}):
    """
    Get color based on KPI value thresholds
    
    Args:
        value: Numeric value to evaluate
        thresholds: Dict with 'high' and 'medium' threshold values
    
    Returns:
        Color string for the value
    """
    if value >= thresholds['high']:
        return COLORS['success']
    elif value >= thresholds['medium']:
        return COLORS['warning']
    else:
        return COLORS['error']


def apply_chart_theme(figure):
    """
    Apply consistent theme to Plotly figure
    
    Args:
        figure: Plotly figure object
    
    Returns:
        Updated figure with theme applied
    """
    figure.update_layout(
        plot_bgcolor=CHART_THEME['plot_bgcolor'],
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        font=CHART_THEME['font'],
        title_font=CHART_THEME['title']['font'],
        xaxis=CHART_THEME['xaxis'],
        yaxis=CHART_THEME['yaxis'],
        colorway=CHART_THEME['colorway'],
        hovermode='closest',
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return figure
