"""
FastAPI Application for AI Procurement Agent
Provides REST API endpoints for agent queries and management.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from agent.agent import agent
from agent.rag.ingestion import ingestion_pipeline
from agent.tools.rag_tools import rag_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Procurement Agent API",
    description="REST API for the AI Procurement Investigation & Recommendation Agent",
    version="1.0.0"
)

# Configure CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class AgentQueryRequest(BaseModel):
    """Request model for agent queries"""
    question: str = Field(..., description="The procurement question to investigate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why is Beta_Supplies performing poorly?"
            }
        }


class AgentQueryResponse(BaseModel):
    """Response model for agent queries"""
    question: str
    answer: str
    evidence: list
    sources: list
    ml_insights_used: bool
    policy_used: bool
    error: Optional[str]
    error_type: Optional[str] = None
    timestamp: str
    processing_time_seconds: float


class StatusResponse(BaseModel):
    """Response model for system status"""
    agent_available: bool
    llm_model: Optional[str]
    num_tools: int
    rag_enabled: bool
    rag_available: bool
    rag_document_count: int
    configuration_valid: bool


class IngestionRequest(BaseModel):
    """Request model for document ingestion"""
    reset: bool = Field(False, description="Reset vector store before ingestion")


class IngestionResponse(BaseModel):
    """Response model for document ingestion"""
    success: bool
    documents_loaded: int
    chunks_created: int
    chunks_stored: int
    errors: list


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Procurement Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/api/agent/query",
            "status": "/api/agent/status",
            "ingest": "/api/agent/ingest",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_available": agent.is_available()
    }


@app.post("/api/agent/query", response_model=AgentQueryResponse)
async def query_agent(request: AgentQueryRequest):
    """
    Query the AI Procurement Agent.
    
    The agent will investigate the question using database tools, ML insights,
    and procurement knowledge (RAG) to provide evidence-based recommendations.
    """
    try:
        # Validate and sanitize question
        question = request.question.strip() if request.question else ""
        logger.info(f"Received query: '{question}'")
        
        # Reject empty questions before calling agent
        if not question:
            logger.warning("Empty question received")
            return AgentQueryResponse(
                question="",
                answer="Please enter a question. I need a question to investigate procurement data and provide recommendations.",
                evidence=[],
                sources=[],
                ml_insights_used=False,
                policy_used=False,
                error="empty_question",
                error_type="VALIDATION_ERROR",
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=0.0
            )
        
        if not agent.is_available():
            raise HTTPException(
                status_code=503,
                detail="Agent is not available. Check configuration and ensure LLM API key is set."
            )
        
        # Process the query with validated question
        response = agent.query(question)
        
        # Check if there was an error
        if response.get('error'):
            error_type = response.get('error_type', 'UNKNOWN')
            
            # For quota exhaustion, return 200 with error in response (not HTTP error)
            # This allows graceful handling in the UI
            if error_type == 'QUOTA_EXHAUSTED':
                logger.warning(f"Query failed due to quota exhaustion: {request.question}")
            elif error_type == 'AUTH_ERROR':
                logger.error("Authentication error - check API key")
            else:
                logger.error(f"Query processing error ({error_type}): {response.get('error')}")
        else:
            logger.info(f"Query processed successfully in {response['processing_time_seconds']:.2f}s")
        
        return AgentQueryResponse(**response)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Query processing failed with exception: {e}", exc_info=True)
        
        # Return user-friendly error
        error_msg = str(e)
        if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
            detail = "The AI service has temporarily reached its request limit. Please try again later."
        elif '401' in error_msg or '403' in error_msg:
            detail = "API authentication failed. Please check your API key configuration."
        else:
            detail = "An unexpected error occurred while processing your question."
        
        raise HTTPException(status_code=500, detail=detail)


@app.get("/api/agent/status", response_model=StatusResponse)
async def get_agent_status():
    """
    Get the status of the AI Procurement Agent.
    
    Returns information about agent availability, configuration,
    and RAG system status.
    """
    try:
        agent_status = agent.get_status()
        rag_status = rag_tools.get_status()
        
        return StatusResponse(
            agent_available=agent_status['available'],
            llm_model=agent_status.get('llm_model'),
            num_tools=agent_status['num_tools'],
            rag_enabled=agent_status['rag_enabled'],
            rag_available=agent_status['rag_available'],
            rag_document_count=rag_status['document_count'],
            configuration_valid=agent_status['configuration_valid']
        )
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/ingest", response_model=IngestionResponse)
async def ingest_documents(request: IngestionRequest, background_tasks: BackgroundTasks):
    """
    Ingest procurement policy documents into the RAG system.
    
    This loads documents from the knowledge_base directory, chunks them,
    generates embeddings, and stores them in the vector database.
    
    - **reset**: If true, clears existing documents before ingestion
    """
    try:
        logger.info(f"Starting document ingestion (reset={request.reset})")
        
        # Run ingestion in background for large document sets
        stats = ingestion_pipeline.ingest(reset=request.reset)
        
        logger.info(f"Ingestion complete: {stats}")
        
        return IngestionResponse(**stats)
        
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/rag/status")
async def get_rag_status():
    """Get detailed RAG system status"""
    try:
        status = rag_tools.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get RAG status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested endpoint does not exist",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please check server logs."
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting AI Procurement Agent API...")
    logger.info("API will be available at: http://localhost:8001")
    logger.info("Documentation: http://localhost:8001/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
