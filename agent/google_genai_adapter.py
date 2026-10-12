"""
Google GenAI SDK Adapter for LangChain Compatibility
Uses the new google-genai SDK (supports AQ authorization keys)
Provides a LangChain-compatible interface for agent integration with tool calling support
"""

from typing import Any, Dict, List, Optional, Callable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from google import genai
from google.genai import types
import logging
import json

logger = logging.getLogger(__name__)


class GoogleGenAIChatModel(BaseChatModel):
    """
    LangChain-compatible chat model using the new Google GenAI SDK.
    
    Supports:
    - AQ authorization keys (new format)
    - AIza standard keys (legacy format)  
    - Model: gemini-3.8-flash (current stable model)
    - Automatic function calling with tools
    """
    
    model: str = "gemini-3.8-flash"
    api_key: str
    temperature: float = 0.1
    max_output_tokens: int = 2000
    client: Optional[Any] = None
    bound_tools: List[Any] = []
    
    def __init__(self, **kwargs):
        """Initialize the Google GenAI chat model"""
        super().__init__(**kwargs)
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"Google GenAI client initialized with model: {self.model}")
    
    @property
    def _llm_type(self) -> str:
        """Return identifier for the LLM type"""
        return "google-genai"
    
    def _langchain_tool_to_python_function(self, tool) -> Callable:
        """
        Convert a LangChain tool to a Python function that Google GenAI SDK can use.
        
        The SDK supports automatic function calling with Python functions.
        We extract the tool's callable and add proper docstring and type hints.
        """
        # Get the tool's function
        tool_func = tool.func if hasattr(tool, 'func') else tool.run
        tool_name = tool.name
        tool_description = tool.description
        
        # Create a wrapper function with proper docstring
        def wrapper_func(query: str = "") -> str:
            f"""{tool_description}
            
            Args:
                query: {tool_description}
            
            Returns:
                str: The tool's result as a string
            """
            try:
                result = tool_func(query)
                return str(result)
            except Exception as e:
                logger.error(f"Tool {tool_name} execution failed: {e}")
                return json.dumps({"error": str(e)})
        
        # Set function name and docstring for the SDK
        wrapper_func.__name__ = tool_name
        wrapper_func.__doc__ = f"{tool_description}\n\nArgs:\n    query: Input query string\n\nReturns:\n    str: Result"
        
        return wrapper_func
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate a response from the model with tool calling support.
        
        Args:
            messages: List of messages in the conversation
            stop: Optional list of stop sequences
            **kwargs: Additional keyword arguments
            
        Returns:
            ChatResult with the model's response
        """
        try:
            # Convert LangChain messages to text input
            input_text = self._messages_to_text(messages)
            
            logger.debug(f"Sending request to {self.model} with {len(self.bound_tools)} tools")
            
            # Prepare config with tools if available
            config_dict = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
            }
            
            # Convert LangChain tools to Python functions for Google GenAI SDK
            python_functions = []
            if self.bound_tools:
                for tool in self.bound_tools:
                    try:
                        func = self._langchain_tool_to_python_function(tool)
                        python_functions.append(func)
                        logger.debug(f"Added tool: {tool.name}")
                    except Exception as e:
                        logger.warning(f"Failed to convert tool {getattr(tool, 'name', 'unknown')}: {e}")
                
                if python_functions:
                    config_dict["tools"] = python_functions
                    # Enable automatic function calling (SDK default behavior)
                    logger.info(f"Enabled {len(python_functions)} tools for automatic function calling")
            
            config = types.GenerateContentConfig(**config_dict)
            
            # Use generate_content API which supports tools
            response = self.client.models.generate_content(
                model=self.model,
                contents=input_text,
                config=config
            )
            
            # Extract response text
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Create LangChain-compatible response
            message = AIMessage(content=response_text)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _messages_to_text(self, messages: List[BaseMessage]) -> str:
        """
        Convert LangChain messages to text input.
        
        The new Google GenAI SDK uses a simpler interaction model.
        We combine system message and conversation history into a single prompt.
        """
        parts = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                parts.append(f"Assistant: {msg.content}")
            elif isinstance(msg, ToolMessage):
                # Tool results
                parts.append(f"Tool Result: {msg.content}")
            else:
                parts.append(str(msg.content))
        
        return "\n\n".join(parts)
    
    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "GoogleGenAIChatModel":
        """
        Bind tools to the model for function calling.
        
        The Google GenAI SDK supports automatic function calling.
        We store the tools and convert them to Python functions when generating.
        
        Args:
            tools: List of LangChain tools
            **kwargs: Additional arguments
            
        Returns:
            Self with tools bound
        """
        # Create a new instance with tools bound
        bound_model = self.__class__(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens
        )
        bound_model.client = self.client
        bound_model.bound_tools = tools
        
        logger.info(f"Bound {len(tools)} tools to model")
        return bound_model
    
    @property  
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters for the model"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "num_tools": len(self.bound_tools),
        }
