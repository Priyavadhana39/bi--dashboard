"""
Module 5: AI Procurement Agent Page
Interactive interface for the AI Procurement Investigation & Recommendation Agent
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import requests
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.components.ui_components import (
    create_page_header, create_alert, create_status_badge
)
from dashboard.styles.design_system import COLORS, SPACING, RADIUS, SHADOWS, COMPONENT_STYLES

# Register the page
dash.register_page(
    __name__,
    path='/ai-procurement-agent',
    name='AI Procurement Agent',
    title='AI Procurement Agent - Procurement Intelligence'
)

logger = logging.getLogger(__name__)

# Agent API configuration
AGENT_API_URL = "http://localhost:8001"


def get_agent_status():
    """Get agent status from API"""
    try:
        response = requests.get(f"{AGENT_API_URL}/api/agent/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        return None


# Sample questions for user convenience
SAMPLE_QUESTIONS = [
    "Why is Beta_Supplies performing poorly?",
    "Are there any abnormal procurement prices?",
    "Which supplier should we consider for Electronics?",
    "What is the expected procurement demand for Electronics?",
    "Why did procurement spending increase?",
    "Find suppliers with poor performance and price anomalies"
]


# Layout
layout = html.Div([
    # Page Header
    create_page_header(
        title='AI Procurement Agent',
        description='Ask natural language questions about procurement data, supplier performance, and get AI-powered recommendations'
    ),
    
    # Status indicator
    html.Div(id='agent-status-indicator', style={'padding': '0'}),
    
    # Main content
    html.Div([
        # Question input area
        html.Div([
            html.Label('Ask a Procurement Question:', style={
                'fontWeight': '600',
                'fontSize': '16px',
                'color': COLORS['text_primary'],
                'marginBottom': SPACING['md'],
                'display': 'block'
            }),
            html.Div([
                dcc.Textarea(
                    id='agent-question-input',
                    placeholder='e.g., Why is Beta_Supplies performing poorly? Which suppliers have delivery issues?',
                    style={
                        'width': '100%',
                        'minHeight': '120px',
                        'padding': SPACING['lg'],
                        'fontSize': '15px',
                        'border': f'2px solid {COLORS["border_light"]}',
                        'borderRadius': RADIUS['md'],
                        'resize': 'vertical',
                        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        'lineHeight': '1.6'
                    }
                ),
            ]),
            html.Div([
                html.Button(
                    [html.Span('🔍 ', style={'marginRight': SPACING['sm']}), 'Investigate'],
                    id='agent-submit-button',
                    n_clicks=0,
                    style={
                        'backgroundColor': COLORS['primary'],
                        'color': 'white',
                        'border': 'none',
                        'padding': f"{SPACING['md']} {SPACING['3xl']}",
                        'fontSize': '15px',
                        'fontWeight': '600',
                        'borderRadius': RADIUS['md'],
                        'cursor': 'pointer',
                        'marginTop': SPACING['lg'],
                        'transition': 'all 0.2s ease',
                        'boxShadow': SHADOWS['sm']
                    }
                ),
                html.Button(
                    [html.Span('🗑️ ', style={'marginRight': SPACING['sm']}), 'Clear'],
                    id='agent-clear-button',
                    n_clicks=0,
                    style={
                        'backgroundColor': COLORS['bg_tertiary'],
                        'color': COLORS['text_secondary'],
                        'border': f'1px solid {COLORS["border_medium"]}',
                        'padding': f"{SPACING['md']} {SPACING['3xl']}",
                        'fontSize': '15px',
                        'fontWeight': '600',
                        'borderRadius': RADIUS['md'],
                        'cursor': 'pointer',
                        'marginTop': SPACING['lg'],
                        'marginLeft': SPACING['md']
                    }
                ),
            ]),
        ], style={**COMPONENT_STYLES['chart_container'], 'marginBottom': SPACING['xl']}),
        
        # Sample questions
        html.Div([
            html.H3('💡 Sample Questions', style={
                'fontSize': '16px',
                'fontWeight': '600',
                'color': COLORS['text_primary'],
                'marginBottom': SPACING['lg']
            }),
            html.Div([
                html.Button(
                    question,
                    id={'type': 'sample-question', 'index': i},
                    n_clicks=0,
                    style={
                        'backgroundColor': COLORS['bg_tertiary'],
                        'color': COLORS['text_secondary'],
                        'border': f'1px solid {COLORS["border_light"]}',
                        'padding': f"{SPACING['sm']} {SPACING['lg']}",
                        'fontSize': '14px',
                        'borderRadius': RADIUS['md'],
                        'cursor': 'pointer',
                        'marginRight': SPACING['sm'],
                        'marginBottom': SPACING['sm'],
                        'display': 'inline-block',
                        'transition': 'all 0.2s'
                    }
                ) for i, question in enumerate(SAMPLE_QUESTIONS)
            ])
        ], style={**COMPONENT_STYLES['chart_container'], 'marginBottom': SPACING['xl']}),
        
        # Loading indicator
        dcc.Loading(
            id='agent-loading',
            type='circle',
            color=COLORS['primary'],
            children=[
                # Response area
                html.Div(id='agent-response-area', style={'marginTop': SPACING['xl']})
            ]
        ),
        
    ]),
    
    # Hidden div to store sample question clicks
    html.Div(id='sample-question-store', style={'display': 'none'})
], style=COMPONENT_STYLES['page_container'])


# Callbacks

@callback(
    Output('agent-status-indicator', 'children'),
    Input('agent-status-indicator', 'id')
)
def update_status_indicator(_):
    """Update agent status indicator"""
    status = get_agent_status()
    
    if not status:
        return create_alert(
            '⚠️ Agent API not available. Make sure the agent API is running on port 8001.',
            alert_type='error'
        )
    
    if not status.get('agent_available'):
        return create_alert(
            '⚠️ Agent not configured. Check that API key is set in .env file.',
            alert_type='error'
        )
    
    rag_status = 'Active' if status.get('rag_available') else 'No documents'
    
    return html.Div([
        html.Span('✅ ', style={'fontSize': '18px', 'marginRight': SPACING['sm']}),
        html.Span(f"Agent Ready", style={
            'color': COLORS['success'],
            'fontSize': '16px',
            'fontWeight': '600',
            'marginRight': SPACING['md']
        }),
        create_status_badge(f"Model: {status.get('llm_model', 'Unknown')}", 'info'),
        html.Span(' ', style={'marginRight': SPACING['sm']}),
        create_status_badge(f"Tools: {status.get('num_tools', 0)}", 'info'),
        html.Span(' ', style={'marginRight': SPACING['sm']}),
        create_status_badge(f"RAG: {rag_status}", 'success' if status.get('rag_available') else 'warning'),
    ], style={
        **COMPONENT_STYLES['chart_container'],
        'display': 'flex',
        'alignItems': 'center',
        'marginBottom': SPACING['xl']
    })


@callback(
    Output('agent-question-input', 'value', allow_duplicate=True),
    Input({'type': 'sample-question', 'index': dash.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def load_sample_question(n_clicks):
    """Load sample question into input"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return dash.no_update
    
    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id']
    
    if 'sample-question' in button_id:
        # Extract index from button_id
        import json
        button_info = json.loads(button_id.split('.')[0])
        index = button_info['index']
        
        if index < len(SAMPLE_QUESTIONS):
            return SAMPLE_QUESTIONS[index]
    
    return dash.no_update


@callback(
    Output('agent-response-area', 'children'),
    Output('agent-question-input', 'value'),
    Input('agent-submit-button', 'n_clicks'),
    Input('agent-clear-button', 'n_clicks'),
    State('agent-question-input', 'value'),
    prevent_initial_call=True
)
def process_question(submit_clicks, clear_clicks, question):
    """Process agent question or clear input"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle clear button
    if button_id == 'agent-clear-button':
        return None, ''
    
    # Handle submit button
    if button_id == 'agent-submit-button':
        # Trim and validate question
        question_trimmed = question.strip() if question else ""
        
        if not question_trimmed:
            return create_alert('⚠️ Please enter a question before clicking Investigate.', alert_type='warning'), dash.no_update
        
        try:
            # Call agent API with trimmed question
            response = requests.post(
                f"{AGENT_API_URL}/api/agent/query",
                json={"question": question_trimmed},
                timeout=120
            )
            
            # Handle all response codes gracefully
            if response.status_code == 200:
                data = response.json()
                # Build response UI (handles errors within response)
                return build_response_ui(data), dash.no_update
            else:
                # HTTP error (4xx, 5xx)
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = f"HTTP {response.status_code} error"
                
                return html.Div([
                    html.H3('❌ Error', style={
                        'color': COLORS['error'],
                        'marginBottom': SPACING['md'],
                        'fontSize': '16px',
                        'fontWeight': '600'
                    }),
                    html.P(f"API Error: {error_detail}", style={
                        'color': COLORS['text_secondary'],
                        'fontSize': '14px'
                    })
                ], style={
                    'backgroundColor': COLORS['error_bg'],
                    'padding': SPACING['xl'],
                    'borderRadius': RADIUS['lg'],
                    'border': f"1px solid {COLORS['error']}"
                }), dash.no_update
            
        except requests.exceptions.Timeout:
            return html.Div([
                html.H3('⏱️ Timeout', style={
                    'color': COLORS['error'],
                    'marginBottom': SPACING['md'],
                    'fontSize': '16px',
                    'fontWeight': '600'
                }),
                html.P('The request took too long. Please try again.', style={
                    'color': COLORS['text_secondary'],
                    'fontSize': '14px'
                })
            ], style={
                'backgroundColor': COLORS['error_bg'],
                'padding': SPACING['xl'],
                'borderRadius': RADIUS['lg'],
                'border': f"1px solid {COLORS['error']}"
            }), dash.no_update
            
        except Exception as e:
            logger.error(f"Agent query failed: {e}")
            return html.Div([
                html.H3('❌ Error', style={
                    'color': COLORS['error'],
                    'marginBottom': SPACING['md'],
                    'fontSize': '16px',
                    'fontWeight': '600'
                }),
                html.P(f"Failed to process question: {str(e)}", style={
                    'color': COLORS['text_secondary'],
                    'fontSize': '14px'
                })
            ], style={
                'backgroundColor': COLORS['error_bg'],
                'padding': SPACING['xl'],
                'borderRadius': RADIUS['lg'],
                'border': f"1px solid {COLORS['error']}"
            }), dash.no_update
    
    return dash.no_update, dash.no_update


def build_response_ui(data):
    """Build the response UI from agent data"""
    children = []
    
    # Question header (only if question is not empty)
    if data.get('question'):
        children.append(html.Div([
            html.H3('Question:', style={
                'fontSize': '16px',
                'fontWeight': '600',
                'color': COLORS['text_primary'],
                'marginBottom': SPACING['md']
            }),
            html.P(data['question'], style={
                'fontSize': '14px',
                'color': COLORS['text_secondary'],
                'fontStyle': 'italic'
            })
        ], style={'marginBottom': SPACING['xl']}))
    
    # Check if there was an error
    error_type = data.get('error_type')
    has_error = data.get('error') is not None
    
    # Build answer section
    if has_error:
        # Determine alert type and icon based on error
        if error_type == 'QUOTA_EXHAUSTED':
            alert_type = 'warning'
            icon = '⏳ '
        elif error_type == 'VALIDATION_ERROR':
            alert_type = 'warning'
            icon = '⚠️ '
        elif error_type in ['AUTH_ERROR', 'MODEL_NOT_FOUND']:
            alert_type = 'error'
            icon = '⚠️ '
        else:
            alert_type = 'error'
            icon = '❌ '
        
        # Error response using alert component
        children.append(html.Div([
            html.H3(f'{icon}Response:', style={
                'fontSize': '16px',
                'fontWeight': '600',
                'color': COLORS['text_primary'],
                'marginBottom': SPACING['md']
            }),
            dcc.Markdown(data['answer'], style={
                'fontSize': '14px',
                'lineHeight': '1.6',
                'color': COLORS['text_primary']
            })
        ], style={
            'backgroundColor': COLORS[f'{alert_type}_bg'],
            'padding': SPACING['xl'],
            'borderRadius': RADIUS['lg'],
            'border': f"2px solid {COLORS[alert_type]}",
            'marginBottom': SPACING['xl']
        }))
        
        # Add helpful message for quota exhaustion
        if error_type == 'QUOTA_EXHAUSTED':
            children.append(html.Div([
                html.H4('💡 What you can do:', style={
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'color': COLORS['text_primary'],
                    'marginBottom': SPACING['md']
                }),
                html.Ul([
                    html.Li('Explore the other dashboard pages for data analytics and insights'),
                    html.Li('Try again later (quota resets within 24 hours)'),
                    html.Li('Check the Gemini API console for quota details'),
                ], style={
                    'fontSize': '13px',
                    'color': COLORS['text_secondary'],
                    'lineHeight': '1.8'
                })
            ], style={
                'backgroundColor': COLORS['bg_secondary'],
                'padding': SPACING['lg'],
                'borderRadius': RADIUS['md'],
                'border': f"1px solid {COLORS['border_light']}",
                'marginBottom': SPACING['xl']
            }))
    else:
        # Successful response
        children.append(html.Div([
            html.H3('✅ Answer:', style={
                'fontSize': '16px',
                'fontWeight': '600',
                'color': COLORS['success'],
                'marginBottom': SPACING['md']
            }),
            dcc.Markdown(data['answer'], style={
                'fontSize': '14px',
                'lineHeight': '1.6',
                'color': COLORS['text_primary']
            })
        ], style={
            'backgroundColor': COLORS['success_bg'],
            'padding': SPACING['xl'],
            'borderRadius': RADIUS['lg'],
            'border': f"1px solid {COLORS['success_light']}",
            'marginBottom': SPACING['xl']
        }))
    
    # Metadata badges (only show for successful responses or if ML insights used)
    if not has_error or (has_error and data.get('ml_insights_used')):
        metadata_items = []
        if data.get('ml_insights_used'):
            metadata_items.append(create_status_badge('🤖 ML Insights Used', 'info'))
            metadata_items.append(html.Span(' ', style={'marginRight': SPACING['sm']}))
        
        if data.get('policy_used'):
            metadata_items.append(create_status_badge('📚 Policy Referenced', 'info'))
            metadata_items.append(html.Span(' ', style={'marginRight': SPACING['sm']}))
        
        metadata_items.append(create_status_badge(
            f"⏱️ {data.get('processing_time_seconds', 0):.1f}s",
            'default'
        ))
        
        if metadata_items:
            children.append(html.Div(metadata_items, style={'marginTop': SPACING['lg']}))
    
    return html.Div(children, style={
        **COMPONENT_STYLES['chart_container'],
        'marginTop': SPACING['xl']
    })
