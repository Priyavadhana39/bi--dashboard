"""
Vector Store for RAG System
Uses ChromaDB for local vector storage and retrieval.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from agent.rag.chunker import DocumentChunk
from agent.config import config

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-based vector store for document retrieval"""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB vector store.
        
        Args:
            persist_directory: Directory to persist the vector database
        """
        self.persist_directory = persist_directory or config.VECTOR_STORE_PATH
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection name for procurement documents
        self.collection_name = "procurement_knowledge"
        self.collection = None
        
        logger.info(f"VectorStore initialized at {self.persist_directory}")
    
    def get_or_create_collection(self):
        """Get or create the document collection"""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Procurement policy and knowledge documents"}
            )
            return self.collection
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            raise
    
    def add_chunks(self, chunks: List[DocumentChunk]):
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of document chunks to add
        """
        if not chunks:
            logger.warning("No chunks to add to vector store")
            return
        
        collection = self.get_or_create_collection()
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk.content)
            metadatas.append({
                'source': chunk.metadata.get('source', 'unknown'),
                'file_type': chunk.metadata.get('file_type', 'unknown'),
                'chunk_id': str(chunk.metadata.get('chunk_id', i))
            })
            # Create unique ID
            source = chunk.metadata.get('source', 'unknown')
            chunk_id = chunk.metadata.get('chunk_id', i)
            ids.append(f"{source}_{chunk_id}")
        
        try:
            # Add to collection (ChromaDB handles embedding automatically)
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(chunks)} chunks to vector store")
        except Exception as e:
            logger.error(f"Failed to add chunks: {e}")
            raise
    
    def query(self, query_text: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant documents.
        
        Args:
            query_text: The query string
            top_k: Number of results to return
            
        Returns:
            List of results with content and metadata
        """
        if top_k is None:
            top_k = config.RETRIEVAL_TOP_K
        
        collection = self.get_or_create_collection()
        
        try:
            # Query the collection
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Retrieved {len(formatted_results)} results for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query vector store: {e}")
            return []
    
    def count_documents(self) -> int:
        """Count the number of chunks in the vector store"""
        try:
            collection = self.get_or_create_collection()
            return collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    def reset(self):
        """Reset the vector store (delete all documents)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info("Vector store reset complete")
        except Exception as e:
            logger.warning(f"Failed to reset vector store: {e}")
    
    def is_empty(self) -> bool:
        """Check if the vector store is empty"""
        return self.count_documents() == 0


# Singleton instance
vector_store = VectorStore()
