"""
AI Procurement Agent
Main agent implementation with tool orchestration and LLM integration.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI  # OLD SDK - doesn't support AQ keys
from agent.google_genai_adapter import GoogleGenAIChatModel  # NEW SDK - supports AQ keys
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from agent.config import config
from agent.tools.database_tools import db_tools
from agent.tools.ml_tools import ml_tools
from agent.tools.rag_tools import rag_tools
from agent.prompts.system_prompt import (
    PROCUREMENT_AGENT_SYSTEM_PROMPT,
    PROCUREMENT_AGENT_USER_PROMPT_TEMPLATE
)

logger = logging.getLogger(__name__)


class ProcurementAgent:
    """AI Procurement Investigation & Recommendation Agent"""
    
    def __init__(self):
        """Initialize the procurement agent"""
        self.llm = None
        self.agent_executor = None
        self.tools = []
        
        # Initialize if configuration is valid
        if config.validate():
            self._initialize_llm()
            self._create_tools()
            self._create_agent()
        else:
            logger.warning("Agent configuration invalid - LLM not initialized")
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider"""
        try:
            if config.LLM_PROVIDER == 'gemini':
                # Use new Google GenAI SDK adapter (supports AQ authorization keys)
                self.llm = GoogleGenAIChatModel(
                    model=config.LLM_MODEL,
                    api_key=config.LLM_API_KEY,
                    temperature=config.LLM_TEMPERATURE,
                    max_output_tokens=config.LLM_MAX_TOKENS
                )
                logger.info(f"Google GenAI LLM initialized: {config.LLM_MODEL}")
                
            elif config.LLM_PROVIDER == 'openai':
                self.llm = ChatOpenAI(
                    model=config.LLM_MODEL,
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS,
                    openai_api_key=config.LLM_API_KEY
                )
                logger.info(f"OpenAI LLM initialized: {config.LLM_MODEL}")
            else:
                raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _validate_gemini_model(self):
        """Validate that the configured Gemini model exists and is accessible"""
        try:
            # Make a minimal test call to validate model
            test_message = HumanMessage(content="test")
            self.llm.invoke([test_message])
            logger.info(f"Gemini model {config.LLM_MODEL} validated successfully")
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg:
                logger.error(f"Model {config.LLM_MODEL} not found. Check model name in .env file.")
                raise ValueError(f"Invalid Gemini model: {config.LLM_MODEL}. Common models: models/gemini-1.5-flash, models/gemini-1.5-pro")
            else:
                logger.warning(f"Could not validate model (may still work): {e}")
    
    def _create_tools(self):
        """Create LangChain tools from our tool classes"""
        
        # Custom JSON encoder for Decimal types
        def json_dumps_with_decimal(obj):
            """Convert object to JSON, handling Decimal types"""
            from decimal import Decimal
            import datetime
            
            def decimal_default(o):
                if isinstance(o, Decimal):
                    return float(o)
                elif isinstance(o, (datetime.date, datetime.datetime)):
                    return o.isoformat()
                raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
            
            return json.dumps(obj, default=decimal_default)
        
        # Helper to create tool functions
        def make_tool(name: str, description: str, func):
            """Create a tool with proper decorator"""
            @tool(name, description=description)
            def tool_func(query: str = "") -> str:
                """Tool function"""
                result = func(query) if query else func("")
                return json_dumps_with_decimal(result) if not isinstance(result, str) else result
            return tool_func
        
        # Database Tools
        self.tools.append(make_tool(
            "get_supplier_info",
            "Get detailed information about a specific supplier including total orders, spend, savings, lead time, defects, and compliance. Input: supplier name",
            lambda supplier: db_tools.get_supplier_info(supplier)
        ))
        
        self.tools.append(make_tool(
            "get_supplier_performance_metrics",
            "Get detailed performance metrics for a supplier: delivery status, lead times, defect rates, compliance, and missing data counts. Input: supplier name",
            lambda supplier: db_tools.get_supplier_performance_metrics(supplier)
        ))
        
        self.tools.append(make_tool(
            "get_all_suppliers",
            "Get list of all suppliers with basic statistics (total orders, spend, savings). Input: empty string or 'all'",
            lambda x: db_tools.get_all_suppliers()
        ))
        
        self.tools.append(make_tool(
            "get_category_info",
            "Get information about a specific item category: total orders, quantity, spend, prices, and supplier count. Input: category name",
            lambda category: db_tools.get_category_info(category)
        ))
        
        self.tools.append(make_tool(
            "get_category_suppliers",
            "Get all suppliers for a category with their performance metrics. Input: category name",
            lambda category: db_tools.get_category_suppliers(category)
        ))
        
        self.tools.append(make_tool(
            "get_spending_by_period",
            "Get spending aggregated by month to analyze spending trends over time. Input: empty string",
            lambda x: db_tools.get_spending_by_period()
        ))
        
        self.tools.append(make_tool(
            "get_spending_by_supplier",
            "Get spending breakdown by supplier. Input: empty string",
            lambda x: db_tools.get_spending_by_supplier()
        ))
        
        self.tools.append(make_tool(
            "get_spending_by_category",
            "Get spending breakdown by category. Input: empty string",
            lambda x: db_tools.get_spending_by_category()
        ))
        
        self.tools.append(make_tool(
            "get_supplier_orders",
            "Get recent purchase orders for a specific supplier. Input: supplier name",
            lambda supplier: db_tools.get_supplier_orders(supplier, limit=50)
        ))
        
        # ML Tools
        self.tools.append(make_tool(
            "get_supplier_scores",
            "Get ML-generated performance scores for all suppliers with rankings and performance categories (Excellent/Good/Average/Poor). Input: empty string",
            lambda x: ml_tools.get_supplier_scores()
        ))
        
        self.tools.append(make_tool(
            "get_supplier_score",
            "Get ML-generated performance score for a specific supplier including rank, category, and detailed metrics. Input: supplier name",
            lambda supplier: ml_tools.get_supplier_score(supplier)
        ))
        
        self.tools.append(make_tool(
            "get_poor_performing_suppliers",
            "Get suppliers with poor performance scores (below 50). Input: empty string",
            lambda x: ml_tools.get_poor_performing_suppliers()
        ))
        
        self.tools.append(make_tool(
            "get_price_anomalies",
            "Get ML-detected price anomalies across all purchase orders. Returns orders flagged as having unusual prices (high or low). Input: empty string",
            lambda x: ml_tools.get_price_anomalies(limit=50)
        ))
        
        self.tools.append(make_tool(
            "get_supplier_anomalies",
            "Get price anomalies for a specific supplier. Input: supplier name",
            lambda supplier: ml_tools.get_supplier_anomalies(supplier)
        ))
        
        self.tools.append(make_tool(
            "get_category_anomalies",
            "Get price anomalies for a specific category. Input: category name",
            lambda category: ml_tools.get_category_anomalies(category)
        ))
        
        self.tools.append(make_tool(
            "get_demand_forecast",
            "Get ML-generated demand forecast for a specific category (or 'Overall' for total demand). Returns predicted quantities with confidence intervals. Input: category name or 'Overall'",
            lambda category: ml_tools.get_demand_forecast(category)
        ))
        
        self.tools.append(make_tool(
            "get_latest_forecasts",
            "Get all latest demand forecasts for all categories. Input: empty string",
            lambda x: ml_tools.get_latest_forecasts()
        ))
        
        # RAG Tools
        self.tools.append(make_tool(
            "retrieve_procurement_policy",
            "Retrieve relevant procurement policy documents and guidelines. Use this for questions about procurement procedures, policies, approval rules, or best practices. Input: search query",
            lambda query: rag_tools.retrieve_policy(query)
        ))
        
        logger.info(f"Created {len(self.tools)} tools for agent")
    
    def _create_agent(self):
        """Create the agent using LangGraph"""
        try:
            # Create system message
            system_message = SystemMessage(content=PROCUREMENT_AGENT_SYSTEM_PROMPT)
            
            # Create agent using LangGraph's create_react_agent
            self.agent_executor = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=system_message
            )
            
            logger.info("Agent executor created successfully with LangGraph")
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Process a procurement question and return a response.
        
        Args:
            question: The user's procurement question
            
        Returns:
            Dict with answer, evidence, sources, and metadata
        """
        start_time = datetime.now()
        
        response = {
            'question': question,
            'answer': '',
            'evidence': [],
            'sources': [],
            'ml_insights_used': False,
            'policy_used': False,
            'error': None,
            'error_type': None,
            'timestamp': start_time.isoformat(),
            'processing_time_seconds': 0
        }
        
        try:
            # Validate question before processing
            if not question or not question.strip():
                logger.warning("Empty or whitespace-only question provided")
                response['error_type'] = 'VALIDATION_ERROR'
                response['error'] = 'empty_question'
                response['answer'] = "Please provide a valid question to investigate."
                return response
            
            if not self.agent_executor:
                raise ValueError("Agent not initialized - check configuration")
            
            # Run the agent with LangGraph API
            messages = [HumanMessage(content=question)]
            result = self.agent_executor.invoke({"messages": messages})
            
            # Extract answer from the last AI message
            if 'messages' in result and len(result['messages']) > 0:
                last_message = result['messages'][-1]
                
                # Handle different content formats
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    
                    # If content is a list of dicts (Gemini format)
                    if isinstance(content, list) and len(content) > 0:
                        if isinstance(content[0], dict) and 'text' in content[0]:
                            response['answer'] = content[0]['text']
                        else:
                            response['answer'] = str(content)
                    # If content is a string
                    elif isinstance(content, str):
                        response['answer'] = content
                    else:
                        response['answer'] = str(content)
                
                # Extract tool usage from messages
                for msg in result['messages']:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get('name', 'unknown')
                            
                            # Track what types of tools were used
                            if 'ml' in tool_name.lower() or 'score' in tool_name.lower() or 'anomaly' in tool_name.lower() or 'forecast' in tool_name.lower():
                                response['ml_insights_used'] = True
                            
                            if 'policy' in tool_name.lower():
                                response['policy_used'] = True
                            
                            response['evidence'].append({
                                'tool': tool_name,
                                'used': True
                            })
            else:
                response['answer'] = "I couldn't generate a response. Please try again."
            
            # Calculate processing time
            end_time = datetime.now()
            response['processing_time_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(f"Query processed successfully in {response['processing_time_seconds']:.2f}s")
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Query processing failed: {error_str}", exc_info=True)
            
            # Handle quota exhaustion gracefully (429, 503, or explicit RESOURCE_EXHAUSTED)
            if ('429' in error_str or '503' in error_str or 
                'RESOURCE_EXHAUSTED' in error_str or 
                'quota' in error_str.lower() or 
                'rate limit' in error_str.lower()):
                response['error_type'] = 'QUOTA_EXHAUSTED'
                response['error'] = 'quota_exceeded'
                response['answer'] = (
                    "⏳ **The AI service has temporarily reached its request limit.**\n\n"
                    "This happens when the daily/hourly quota for the Gemini API is exhausted. "
                    "The quota typically resets within 24 hours.\n\n"
                    "**What you can do:**\n"
                    "- Explore the other dashboard pages for procurement analytics and insights\n"
                    "- Try again later when the quota resets\n"
                    "- Check the Gemini API console for quota details"
                )
                logger.warning("Gemini API quota exhausted - returning user-friendly message")
            
            # Handle authentication errors
            elif '401' in error_str or '403' in error_str or 'authentication' in error_str.lower() or 'api key' in error_str.lower():
                response['error_type'] = 'AUTH_ERROR'
                response['error'] = 'authentication_failed'
                response['answer'] = (
                    "API authentication failed. Please check that your API key is valid and properly configured."
                )
                logger.error("API authentication error")
            
            # Handle model not found errors
            elif '404' in error_str or 'not found' in error_str.lower():
                response['error_type'] = 'MODEL_NOT_FOUND'
                response['error'] = 'invalid_model'
                response['answer'] = (
                    f"The configured model '{config.LLM_MODEL}' was not found. "
                    "Please check your model configuration in the .env file."
                )
                logger.error(f"Model not found: {config.LLM_MODEL}")
            
            # Handle timeout errors
            elif 'timeout' in error_str.lower():
                response['error_type'] = 'TIMEOUT'
                response['error'] = 'request_timeout'
                response['answer'] = (
                    "The request took too long to process. Please try again with a simpler question."
                )
                logger.warning("Request timeout")
            
            # Generic error handling
            else:
                response['error_type'] = 'UNKNOWN'
                response['error'] = 'processing_failed'
                response['answer'] = (
                    "I encountered an error while processing your question. "
                    "Please try again or contact support if the issue persists."
                )
                logger.error(f"Unknown error during query processing: {error_str}")
            
            # Calculate processing time even for errors
            end_time = datetime.now()
            response['processing_time_seconds'] = (end_time - start_time).total_seconds()
        
        return response
    
    def is_available(self) -> bool:
        """Check if the agent is available for queries"""
        return self.agent_executor is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            'available': self.is_available(),
            'llm_model': config.LLM_MODEL if self.llm else None,
            'num_tools': len(self.tools),
            'rag_enabled': config.ENABLE_RAG,
            'rag_available': rag_tools.is_available(),
            'configuration_valid': config.validate()
        }


# Singleton instance
agent = ProcurementAgent()
