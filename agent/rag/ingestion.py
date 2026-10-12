"""
Document Ingestion Pipeline
Loads, chunks, embeds, and stores procurement policy documents.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from agent.rag.document_loader import DocumentLoader
from agent.rag.chunker import DocumentChunker
from agent.rag.vector_store import vector_store
from agent.config import config

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Complete pipeline for ingesting documents into RAG system"""
    
    def __init__(self):
        self.knowledge_base_path = config.KNOWLEDGE_BASE_PATH
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        
        self.loader = DocumentLoader(self.knowledge_base_path)
        self.chunker = DocumentChunker(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def ingest(self, reset: bool = False) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline.
        
        Args:
            reset: If True, clear existing vector store before ingesting
            
        Returns:
            Dict with ingestion statistics
        """
        logger.info("Starting document ingestion pipeline...")
        
        stats = {
            'success': False,
            'documents_loaded': 0,
            'chunks_created': 0,
            'chunks_stored': 0,
            'errors': []
        }
        
        try:
            # Reset vector store if requested
            if reset:
                logger.info("Resetting vector store...")
                vector_store.reset()
            
            # Load documents
            logger.info(f"Loading documents from {self.knowledge_base_path}...")
            documents = self.loader.load_documents()
            stats['documents_loaded'] = len(documents)
            
            if not documents:
                logger.warning("No documents found to ingest")
                stats['errors'].append("No documents found in knowledge base")
                return stats
            
            logger.info(f"Loaded {len(documents)} documents")
            
            # Chunk documents
            logger.info("Chunking documents...")
            chunks = self.chunker.chunk_documents(documents)
            stats['chunks_created'] = len(chunks)
            
            if not chunks:
                logger.warning("No chunks created")
                stats['errors'].append("Failed to create chunks from documents")
                return stats
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Store in vector store
            logger.info("Storing chunks in vector database...")
            vector_store.add_chunks(chunks)
            stats['chunks_stored'] = vector_store.count_documents()
            
            logger.info(f"Successfully ingested {stats['chunks_stored']} chunks")
            stats['success'] = True
            
        except Exception as e:
            logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
            stats['errors'].append(str(e))
        
        return stats
    
    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a single file.
        
        Args:
            file_path: Path to the file to ingest
            
        Returns:
            Dict with ingestion statistics
        """
        logger.info(f"Ingesting single file: {file_path}")
        
        stats = {
            'success': False,
            'documents_loaded': 0,
            'chunks_created': 0,
            'chunks_stored': 0,
            'errors': []
        }
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                stats['errors'].append(f"File not found: {file_path}")
                return stats
            
            # Load the file
            if file_path.suffix == '.txt':
                document = self.loader.load_text_file(file_path)
            elif file_path.suffix == '.md':
                document = self.loader.load_markdown_file(file_path)
            elif file_path.suffix == '.pdf':
                document = self.loader.load_pdf_file(file_path)
            elif file_path.suffix == '.docx':
                document = self.loader.load_docx_file(file_path)
            else:
                stats['errors'].append(f"Unsupported file type: {file_path.suffix}")
                return stats
            
            if not document:
                stats['errors'].append("Failed to load document")
                return stats
            
            stats['documents_loaded'] = 1
            
            # Chunk the document
            chunks = self.chunker.chunk_document(document)
            stats['chunks_created'] = len(chunks)
            
            # Store chunks
            vector_store.add_chunks(chunks)
            stats['chunks_stored'] = len(chunks)
            
            logger.info(f"Successfully ingested file: {file_path.name}")
            stats['success'] = True
            
        except Exception as e:
            logger.error(f"Failed to ingest file {file_path}: {e}")
            stats['errors'].append(str(e))
        
        return stats


# Singleton instance
ingestion_pipeline = DocumentIngestionPipeline()
