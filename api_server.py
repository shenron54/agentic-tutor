#!/usr/bin/env python3
"""
FastAPI Server for Agentic Tutor
Simple REST endpoints for external integration with Server-Sent Events streaming
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import sys
import os
from datetime import datetime

# Add the agentic-tutor src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agentic-tutor', 'src'))

from agent.runner import TutorWorkflowRunner
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.types import Command


def serialize_for_sse(obj):
    """
    Recursively serialize objects for Server-Sent Events (SSE).
    Handles LangChain BaseMessage objects by converting them to dictionaries.
    
    Args:
        obj: Any Python object
        
    Returns:
        JSON-serializable version of the object
    """
    # Handle BaseMessage objects (HumanMessage, AIMessage, etc.)
    if isinstance(obj, BaseMessage):
        # Use Pydantic's model_dump() to convert to dict
        return obj.model_dump()
    
    # Handle dictionaries recursively
    elif isinstance(obj, dict):
        return {key: serialize_for_sse(value) for key, value in obj.items()}
    
    # Handle lists and tuples recursively
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_sse(item) for item in obj]
    
    # Handle other Pydantic models (if any)
    elif hasattr(obj, 'model_dump'):
        return obj.model_dump()
    
    # Handle datetime objects
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    
    # Return as-is if already serializable
    else:
        return obj


# Initialize FastAPI app
app = FastAPI(
    title="Agentic Tutor API",
    version="1.0.0",
    description="AI-powered tutoring system with streaming support"
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class StartSessionRequest(BaseModel):
    """Request model for starting a new tutoring session"""
    topic: str = Field(..., description="The topic to learn about", min_length=1)
    stream_tokens: bool = Field(default=True, description="Enable token-level streaming")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Neural Networks",
                "stream_tokens": True
            }
        }


class ResumeSessionRequest(BaseModel):
    """Request model for resuming a session with user response"""
    action: str = Field(..., description="Action type: 'continue', 'ask_question', 'regenerate', etc.")
    question: Optional[str] = Field(None, description="User's question (if action is 'ask_question')")
    selected_prerequisites: Optional[List[str]] = Field(None, description="Selected prerequisites (if action is 'select_prerequisites')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "continue",
                "question": None
            }
        }


class SessionStateResponse(BaseModel):
    """Response model for session state queries"""
    success: bool
    state: Dict[str, Any]
    interrupt: Optional[Dict[str, Any]]
    workflow_stage: Optional[str]


# In-memory store for workflow runners (simple session management)
# In production, consider using Redis or a proper session store
workflow_runners: Dict[str, TutorWorkflowRunner] = {}


def get_or_create_runner(session_id: str) -> TutorWorkflowRunner:
    """Get existing runner or create new one for session"""
    if session_id not in workflow_runners:
        workflow_runners[session_id] = TutorWorkflowRunner(use_checkpointer=True)
    return workflow_runners[session_id]


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Agentic Tutor API",
        "version": "1.0.0",
        "description": "AI-powered tutoring system with streaming support",
        "endpoints": {
            "start_session": "/tutor/stream/{session_id}",
            "resume_session": "/tutor/resume/{session_id}",
            "get_state": "/tutor/state/{session_id}",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(workflow_runners)
    }


@app.post("/tutor/stream/{session_id}")
async def stream_tutor_session(session_id: str, request: StartSessionRequest):
    """
    Start a new tutoring session with Server-Sent Events streaming
    
    Returns real-time updates including:
    - LLM token streaming
    - Node completion events
    - Interrupt notifications
    - Errors
    """
    
    async def event_generator():
        """Generate Server-Sent Events for the tutoring session"""
        try:
            # Get or create workflow runner for this session
            runner = get_or_create_runner(session_id)
            
            # Create session config
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "stream_tokens": request.stream_tokens
                }
            }
            
            # Create initial state
            initial_state = {
                "initial_topic": request.topic,
                "messages": [HumanMessage(content=f"I want to learn about {request.topic}")],
                "workflow_stage": "start"
            }
            
            # Send session started event
            yield f"data: {json.dumps({'type': 'session_started', 'topic': request.topic, 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Stream events from the workflow
            async for event in runner.stream_with_llm_tokens(initial_state, config):
                # Serialize event data (handles BaseMessage objects)
                serializable_event = serialize_for_sse(event)
                
                event_data = {
                    **serializable_event,
                    "session_id": session_id,
                    "timestamp": serializable_event.get("timestamp", datetime.now().isoformat())
                }
                yield f"data: {json.dumps(event_data)}\n\n"
            
            # Check for interrupts after streaming completes
            state_result = runner.get_session_state(config)
            if state_result.get("success") and state_result.get("interrupt"):
                # Serialize interrupt data too
                interrupt_event = serialize_for_sse({
                    "type": "interrupt",
                    "interrupt_data": state_result["interrupt"],
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
                yield f"data: {json.dumps(interrupt_event)}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'stream_complete', 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"
                
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
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


@app.post("/tutor/resume/{session_id}")
async def resume_tutor_session(session_id: str, request: ResumeSessionRequest):
    """
    Resume a tutoring session with user response
    
    Returns the updated session state and any new interrupts
    """
    try:
        # Get existing runner
        if session_id not in workflow_runners:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        runner = workflow_runners[session_id]
        
        # Create config
        config = {
            "configurable": {
                "thread_id": session_id,
                "stream_tokens": False  # Resume doesn't need streaming by default
            }
        }
        
        # Build user response based on action
        user_response = {
            "action": request.action
        }
        
        if request.question:
            user_response["question"] = request.question
        
        if request.selected_prerequisites:
            user_response["selected_prerequisites"] = request.selected_prerequisites
        
        # Resume workflow
        result = await runner.resume_with_response(user_response, config)
        
        if result.get("success"):
            return {
                "success": True,
                "session_id": session_id,
                "state": result.get("state", {}),
                "interrupt": result.get("interrupt"),
                "workflow_completed": result.get("workflow_completed", False),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error resuming session: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tutor/state/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """
    Get the current state of a tutoring session
    
    Returns the current workflow state, any active interrupts, and metadata
    """
    try:
        # Get existing runner
        if session_id not in workflow_runners:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        runner = workflow_runners[session_id]
        
        # Create config
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        # Get state
        state_result = runner.get_session_state(config)
        
        if state_result.get("success"):
            state = state_result.get("state", {})
            return SessionStateResponse(
                success=True,
                state=state,
                interrupt=state_result.get("interrupt"),
                workflow_stage=state.get("workflow_stage")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting state: {state_result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tutor/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a tutoring session and free resources
    """
    if session_id in workflow_runners:
        del workflow_runners[session_id]
        return {
            "success": True,
            "message": f"Session {session_id} deleted",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    print("🚀 Starting Agentic Tutor API Server...")
    print("📚 API Documentation available at: http://localhost:8000/docs")
    print("🔍 Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

