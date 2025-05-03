"""
FastAPI server for the 8051 embedded system design agent.
"""

import os
import json
import traceback
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import the agent
from agent.main_agent import EmbeddedDesignAgent

# Initialize FastAPI app
app = FastAPI(
    title="8051 Embedded System Design Agent API",
    description="API for automating the design of 8051 embedded systems",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track the status of design tasks
design_tasks = {}

# Initialize the agent with OpenAI API key from environment variable
try:
    agent = EmbeddedDesignAgent(
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        verbose=True
    )
    print("Agent initialized successfully")
except Exception as e:
    print(f"Error initializing agent: {str(e)}")
    print(traceback.format_exc())
    agent = None

class DesignRequest(BaseModel):
    """Model for design requests."""
    request: str


class DesignResponse(BaseModel):
    """Model for design responses."""
    task_id: str
    status: str
    message: str


class DesignStatus(BaseModel):
    """Model for design status."""
    task_id: str
    status: str
    response: Optional[str] = None
    artifacts: Optional[Dict[str, str]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "8051 Embedded System Design Agent API"}


@app.post("/design")
async def create_design(request: DesignRequest, background_tasks: BackgroundTasks):
    """Create a new design task."""
    if agent is None:
        return DesignResponse(
            task_id="error",
            status="failed",
            message="Agent not initialized. Check server logs for details."
        )
    
    # Generate a task ID
    import uuid
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    design_tasks[task_id] = {
        "status": "pending",
        "request": request.request,
        "response": None,
        "artifacts": None,
        "error": None
    }
    
    # Run the design task in the background
    background_tasks.add_task(run_design_task, task_id, request.request)
    
    return DesignResponse(
        task_id=task_id,
        status="pending",
        message="Design task created and running in the background"
    )


@app.get("/design/{task_id}")
async def get_design_status(task_id: str):
    """Get the status of a design task."""
    if task_id not in design_tasks:
        return DesignStatus(
            task_id=task_id,
            status="failed",
            error="Task not found"
        )
    
    task = design_tasks[task_id]
    
    return DesignStatus(
        task_id=task_id,
        status=task["status"],
        response=task.get("response"),
        artifacts=task.get("artifacts"),
        error=task.get("error")
    )


@app.get("/artifacts/{task_id}/{artifact_type}")
async def get_artifact(task_id: str, artifact_type: str):
    """Get a specific artifact from a design task."""
    if task_id not in design_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = design_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    if "artifacts" not in task or not task["artifacts"]:
        raise HTTPException(status_code=404, detail="No artifacts available")
    
    if artifact_type not in task["artifacts"]:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_type} not found")
    
    file_path = task["artifacts"][artifact_type]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Artifact file not found at {file_path}")
    
    return FileResponse(file_path)


def run_design_task(task_id: str, request: str):
    """Run a design task."""
    if agent is None:
        design_tasks[task_id].update({
            "status": "failed",
            "error": "Agent not initialized. Check server logs for details."
        })
        return
    
    try:
        # Update status to running
        design_tasks[task_id]["status"] = "running"
        print(f"Processing task {task_id} with request: {request}")
        
        # Run the agent
        result = agent.run(request)
        print(f"Agent result for task {task_id}: {result}")
        
        if result.get("success", False):
            # Update status to completed
            design_tasks[task_id].update({
                "status": "completed",
                "response": result.get("response", "Task completed successfully but no response was provided."),
                "artifacts": result.get("artifacts", {})
            })
            print(f"Task {task_id} completed successfully")
        else:
            # Update status to failed
            design_tasks[task_id].update({
                "status": "failed",
                "error": result.get("error", "Unknown error occurred")
            })
            print(f"Task {task_id} failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"Exception in task {task_id}: {str(e)}")
        print(traceback.format_exc())
        # Update status to failed
        design_tasks[task_id].update({
            "status": "failed",
            "error": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 