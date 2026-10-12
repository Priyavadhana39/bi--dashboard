"""
Agent Configuration
Manages LLM, database, and RAG settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentConfig:
    """Configuration for the AI Procurement Agent"""
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv('LLM_PROVIDER', 'gemini')  # openai, gemini, anthropic
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gemini-pro')
    
    # API Keys for different providers
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    ANTHROPIC_API_KEY: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    
    # Determine which API key to use based on provider
    @property
    def LLM_API_KEY(self) -> Optional[str]:
        """Get the appropriate API key based on provider"""
        if self.LLM_PROVIDER == 'openai':
            return self.OPENAI_API_KEY
        elif self.LLM_PROVIDER == 'gemini':
            return self.GEMINI_API_KEY
        elif self.LLM_PROVIDER == 'anthropic':
            return self.ANTHROPIC_API_KEY
        return None
    
    LLM_TEMPERATURE: float = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    LLM_MAX_TOKENS: int = int(os.getenv('LLM_MAX_TOKENS', '2000'))
    
    # Database Configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'procurement_intelligence')
    DB_USER: str = os.getenv('DB_USER', '')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # RAG Configuration
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    VECTOR_STORE_PATH: str = os.getenv('VECTOR_STORE_PATH', './agent/vector_store')
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '1000'))
    CHUNK_OVERLAP: int = int(os.getenv('CHUNK_OVERLAP', '200'))
    RETRIEVAL_TOP_K: int = int(os.getenv('RETRIEVAL_TOP_K', '3'))
    
    # Agent Configuration
    MAX_TOOL_CALLS: int = int(os.getenv('MAX_TOOL_CALLS', '10'))
    ENABLE_RAG: bool = os.getenv('ENABLE_RAG', 'true').lower() == 'true'
    
    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = './agent/knowledge_base'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        # Check if appropriate API key exists for selected provider
        config_instance = cls()
        if not config_instance.LLM_API_KEY:
            return False
        if not cls.DB_USER:
            return False
        return True
    
    @classmethod
    def get_db_connection_string(cls) -> str:
        """Get database connection string"""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"


# Singleton instance
config = AgentConfig()
