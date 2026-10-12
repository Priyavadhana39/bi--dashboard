"""
RAG Tools for AI Agent
Retrieval-Augmented Generation tools for procurement knowledge.
"""

from typing import List, Dict, Any, Optional
import logging
from agent.rag.retriever import retriever
from agent.config import config

logger = logging.getLogger(__name__)


class RAGTools:
    """RAG tools for the AI agent"""
    
    def __init__(self):
        self.retriever = retriever
    
    def retrieve_policy(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Retrieve relevant procurement policy documents.
        
        Args:
            query: The query about procurement policy
            top_k: Number of results to return
            
        Returns:
            Dict with retrieved documents and formatted context
        """
        if not config.ENABLE_RAG:
            return {
                'has_results': False,
                'message': 'RAG system is disabled',
                'documents': [],
                'sources': []
            }
        
        try:
            result = self.retriever.retrieve_with_context(query, top_k)
            return result
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return {
                'has_results': False,
                'message': f'Retrieval failed: {str(e)}',
                'documents': [],
                'sources': []
            }
    
    def is_available(self) -> bool:
        """Check if RAG system is available"""
        return self.retriever.is_available()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of RAG system"""
        from agent.rag.vector_store import vector_store
        
        return {
            'enabled': config.ENABLE_RAG,
            'available': self.is_available(),
            'document_count': vector_store.count_documents(),
            'vector_store_path': config.VECTOR_STORE_PATH,
            'knowledge_base_path': config.KNOWLEDGE_BASE_PATH
        }


# Singleton instance
rag_tools = RAGTools()
