"""FastAPI application for the Deep Research Agent."""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from research_agent.agent.research_agent import DeepResearchAgent
from research_agent.agent.callbacks import ResearchStreamingCallback
from research_agent.utils.config import get_config
from research_agent.utils.logger import get_logger


logger = get_logger(__name__)


# Request/Response Models
class ResearchRequest(BaseModel):
    """Request model for research endpoint."""
    query: str = Field(min_length=1, max_length=500, description="Research query")
    user_id: Optional[str] = Field(default=None, description="User identifier for memory isolation")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    config: dict


# Global agent instance
_agent: Optional[DeepResearchAgent] = None


def get_agent() -> DeepResearchAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        config = get_config()
        
        # Initialize LLM based on configuration
        if config.llm_provider == "openai":
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=config.openai_api_key
            )
            logger.info("Initialized OpenAI LLM")
        else:
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,
                api_key=config.anthropic_api_key
            )
            logger.info("Initialized Anthropic LLM")
        
        # Create agent
        _agent = DeepResearchAgent(
            llm=llm,
            search_provider=config.search_provider
        )
        logger.info("Deep Research Agent initialized")
    
    return _agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting Deep Research Agent API")
    try:
        config = get_config()
        logger.info(f"Configuration loaded: provider={config.search_provider}, max_tool_calls={config.max_tool_calls}")
        
        # Initialize agent
        get_agent()
        logger.info("Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Deep Research Agent API")


# Create FastAPI app
app = FastAPI(
    title="Deep Research Agent API",
    description="Autonomous AI-powered research agent with multi-step planning and execution",
    version="1.0.0",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(
            f"Unhandled error in {request.method} {request.url.path}: {str(e)}",
            exc_info=True,
            extra={"context": {
                "method": request.method,
                "path": request.url.path,
                "error": str(e)
            }}
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all API requests."""
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={"context": {
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        }}
    )
    
    response = await call_next(request)
    
    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code}",
        extra={"context": {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        }}
    )
    
    return response


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "name": "Deep Research Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "research_stream": "/research/stream (POST)"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns application status and configuration.
    """
    try:
        config = get_config()
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            config={
                "search_provider": config.search_provider,
                "max_tool_calls": config.max_tool_calls,
                "max_research_tasks": config.max_research_tasks,
                "log_level": config.log_level
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/research/stream")
async def research_stream(request: ResearchRequest):
    """
    Stream research progress via Server-Sent Events (SSE).
    
    Executes autonomous research on the provided query and streams
    real-time progress updates including:
    - Research plan creation
    - Tool execution (web search, code execution, memory search)
    - Agent actions and decisions
    - Final research results
    
    Args:
        request: ResearchRequest with query and optional user_id
        
    Returns:
        StreamingResponse with Server-Sent Events
    """
    logger.info(
        f"Starting research stream",
        extra={"context": {
            "query": request.query,
            "user_id": request.user_id
        }}
    )
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events for research progress."""
        event_queue: asyncio.Queue = asyncio.Queue()
        
        try:
            # Create streaming callback
            callback = ResearchStreamingCallback(event_queue)
            
            # Get agent with streaming callback
            agent = get_agent()
            agent.stream_handler = callback
            
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'query': request.query})}\n\n"
            
            # Start research in background task
            research_task = asyncio.create_task(
                agent.research(
                    query=request.query,
                    user_id=request.user_id
                )
            )
            
            # Stream events from queue
            while not research_task.done():
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(
                        event_queue.get(),
                        timeout=0.5
                    )
                    
                    # Send event to client
                    yield f"data: {json.dumps(event)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
                    continue
            
            # Get final result
            try:
                result = await research_task
                
                # Send final result event
                final_event = {
                    "type": "complete",
                    "result": {
                        "query": result.query,
                        "text": result.text,
                        "sources": [
                            {
                                "title": s.title,
                                "url": s.url,
                                "content": s.content[:500],  # Truncate for streaming
                                "published_date": s.published_date
                            }
                            for s in result.sources
                        ],
                        "charts_count": len(result.charts),
                        "sources_count": len(result.sources),
                        "execution_time": result.execution_time
                    }
                }
                
                yield f"data: {json.dumps(final_event)}\n\n"
                
                logger.info(
                    f"Research completed successfully",
                    extra={"context": {
                        "query": request.query,
                        "sources_count": len(result.sources),
                        "execution_time": result.execution_time
                    }}
                )
                
            except Exception as e:
                logger.error(
                    f"Research task failed: {str(e)}",
                    exc_info=True,
                    extra={"context": {
                        "query": request.query,
                        "error": str(e)
                    }}
                )
                
                # Send error event
                error_event = {
                    "type": "error",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                yield f"data: {json.dumps(error_event)}\n\n"
            
        except Exception as e:
            logger.error(
                f"Stream generation failed: {str(e)}",
                exc_info=True,
                extra={"context": {
                    "query": request.query,
                    "error": str(e)
                }}
            )
            
            # Send error event
            error_event = {
                "type": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "research_agent.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
