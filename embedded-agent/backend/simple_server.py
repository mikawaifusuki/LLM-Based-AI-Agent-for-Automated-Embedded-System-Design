"""
Simple FastAPI server for testing the frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

# Initialize FastAPI app
app = FastAPI(
    title="8051 Embedded System Design Agent API - Test Server",
    description="Simple API for testing the frontend",
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
    response: str | None = None
    artifacts: dict | None = None
    error: str | None = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "8051 Embedded System Design Agent API - Test Server"}


@app.post("/design")
async def create_design(request: DesignRequest):
    """Create a new design task."""
    # Generate a task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    design_tasks[task_id] = {
        "status": "pending",
        "request": request.request,
        "response": None,
        "artifacts": None,
        "error": None
    }
    
    # For testing, immediately set to completed
    design_tasks[task_id].update({
        "status": "completed",
        "response": f"Successfully processed request: {request.request}",
        "artifacts": {
            "c_source": "/path/to/fake_source.c",
            "firmware_hex": "/path/to/fake_firmware.hex",
            "circuit_dsn": "/path/to/fake_circuit.dsn"
        }
    })
    
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


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 