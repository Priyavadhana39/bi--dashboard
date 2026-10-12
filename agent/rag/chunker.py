"""
Document Chunker for RAG System
Splits documents into meaningful chunks for embedding and retrieval.
"""

from typing import List, Dict, Any
import logging
from agent.rag.document_loader import Document

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of a document"""
    
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
    
    def __repr__(self):
        return f"Chunk(source={self.metadata.get('source', 'unknown')}, chunk_id={self.metadata.get('chunk_id', '?')})"


class DocumentChunker:
    """Split documents into chunks for embedding"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Args:
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_documents(self, documents: List[Document]) -> List[DocumentChunk]:
        """Split documents into chunks"""
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks
    
    def chunk_document(self, document: Document) -> List[DocumentChunk]:
        """Split a single document into chunks"""
        chunks = []
        content = document.content
        
        # Split by paragraphs first for better semantic boundaries
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        chunk_id = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph exceeds chunk size, save current chunk
            if len(current_chunk) + len(paragraph) + 2 > self.chunk_size and current_chunk:
                # Save the current chunk
                chunk_metadata = {
                    **document.metadata,
                    'chunk_id': chunk_id,
                    'chunk_size': len(current_chunk)
                }
                chunks.append(DocumentChunk(content=current_chunk, metadata=chunk_metadata))
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + "\n\n" + paragraph
                chunk_id += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it exists
        if current_chunk:
            chunk_metadata = {
                **document.metadata,
                'chunk_id': chunk_id,
                'chunk_size': len(current_chunk)
            }
            chunks.append(DocumentChunk(content=current_chunk, metadata=chunk_metadata))
        
        return chunks
    
    def chunk_by_sentences(self, document: Document) -> List[DocumentChunk]:
        """Alternative: chunk by sentences for finer granularity"""
        chunks = []
        content = document.content
        
        # Simple sentence splitting (can be improved with NLTK)
        sentences = content.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
        
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunk_metadata = {
                    **document.metadata,
                    'chunk_id': chunk_id,
                    'chunk_size': len(current_chunk)
                }
                chunks.append(DocumentChunk(content=current_chunk, metadata=chunk_metadata))
                
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + " " + sentence
                chunk_id += 1
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunk_metadata = {
                **document.metadata,
                'chunk_id': chunk_id,
                'chunk_size': len(current_chunk)
            }
            chunks.append(DocumentChunk(content=current_chunk, metadata=chunk_metadata))
        
        return chunks
