"""
Document Retriever for RAG System
Retrieves relevant procurement knowledge based on queries.
"""

from typing import List, Dict, Any, Optional
import logging
from agent.rag.vector_store import vector_store
from agent.config import config

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Retrieve relevant documents for RAG"""
    
    def __init__(self, vector_store_instance=None):
        """
        Initialize the retriever.
        
        Args:
            vector_store_instance: VectorStore instance (uses singleton if None)
        """
        self.vector_store = vector_store_instance or vector_store
        self.top_k = config.RETRIEVAL_TOP_K
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            top_k: Number of results to return (uses config default if None)
            
        Returns:
            List of relevant document chunks with metadata
        """
        if top_k is None:
            top_k = self.top_k
        
        # Check if vector store is empty
        if self.vector_store.is_empty():
            logger.warning("Vector store is empty - no documents to retrieve")
            return []
        
        try:
            results = self.vector_store.query(query, top_k=top_k)
            
            if not results:
                logger.info(f"No relevant documents found for query: {query}")
                return []
            
            logger.info(f"Retrieved {len(results)} relevant documents")
            return results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def retrieve_with_context(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Retrieve documents and format them with context for the LLM.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            Dict with retrieved documents and summary
        """
        results = self.retrieve(query, top_k)
        
        if not results:
            return {
                'has_results': False,
                'documents': [],
                'context_text': 'No relevant procurement policy documents found in knowledge base.',
                'sources': []
            }
        
        # Format context text
        context_parts = []
        sources = set()
        
        for i, result in enumerate(results, 1):
            content = result['content']
            source = result['metadata'].get('source', 'Unknown')
            chunk_id = result['metadata'].get('chunk_id', '?')
            
            context_parts.append(f"[Document {i} - {source} (chunk {chunk_id})]:\n{content}\n")
            sources.add(source)
        
        context_text = "\n---\n".join(context_parts)
        
        return {
            'has_results': True,
            'documents': results,
            'context_text': context_text,
            'sources': list(sources),
            'num_results': len(results)
        }
    
    def is_available(self) -> bool:
        """Check if RAG retrieval is available"""
        if not config.ENABLE_RAG:
            return False
        
        if self.vector_store.is_empty():
            return False
        
        return True


# Singleton instance
retriever = DocumentRetriever()
