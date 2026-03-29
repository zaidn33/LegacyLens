"""
FastAPI server exposing the LegacyLens pipeline via LangGraph.
"""

import uuid
from typing import Any

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.state import PipelineState
from backend.graph import build_pipeline_graph
from backend.analyst import AnalystAgent
from backend.coder import CoderAgent
from backend.reviewer import ReviewerAgent
from backend.provider import MockProvider


app = FastAPI(title="LegacyLens Pipeline API", version="1.0.0")

# In-memory job tracker explicitly typed mapping strings to job states
jobs: dict[str, dict[str, Any]] = {}

class JobStatusResponse(BaseModel):
    """Data contract for polling job status and retrieving results."""
    job_id: str
    status: str
    current_node: str | None = None
    iteration: int = 0
    result: dict | None = None
    error: str | None = None


# Initialize agents with MockProvider for Phase 3
provider = MockProvider()
analyst = AnalystAgent(provider)
coder = CoderAgent(provider)
reviewer = ReviewerAgent(provider)

# Compile LangGraph execution graph once
pipeline_graph = build_pipeline_graph(analyst, coder, reviewer)


def _run_graph(job_id: str, source_code: str, file_name: str) -> None:
    """Executes the LangGraph pipeline in the background and mutates job state."""
    jobs[job_id]["status"] = "processing"

    initial_state = PipelineState(
        source_code=source_code,
        file_name=file_name,
        logic_map=None,
        coder_output=None,
        reviewer_output=None,
        result=None,
        iterations=0,
        error=None,
    )

    try:
        # Stream events from the graph execution to update 'current_node'
        for event in pipeline_graph.stream(initial_state):
            # 'event' dict format: {"analyst_node": {"logic_map": ...}}
            for node_name, state_update in event.items():
                jobs[job_id]["current_node"] = node_name
                
                # Update iteration tracker if coder stepped
                if "iterations" in state_update:
                    jobs[job_id]["iteration"] = state_update["iterations"]
                    
                # Handle agent-level crashes gracefully
                if "error" in state_update and state_update["error"]:
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error"] = state_update["error"]
                    return
                
                # Check if reviewer finalized the graph by dropping 'result' in state
                if "result" in state_update and state_update["result"] is not None:
                    jobs[job_id]["status"] = "completed"
                    # Serialize the PipelineResult Pydantic payload for API JSON
                    result_obj = state_update["result"]
                    jobs[job_id]["result"] = result_obj.model_dump()
                    
                    # Persist artifacts into run history
                    from backend.pipeline import save_run_history
                    save_run_history(result_obj, base_dir="runs", job_id=job_id)
                    
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"Graph execution crashed: {str(e)}"


@app.post("/api/v1/jobs", tags=["Jobs"])
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> dict[str, str]:
    """Submit a COBOL file to spawn a new modernization job."""
    content = await file.read()
    source_code = content.decode("utf-8", errors="replace")
    
    job_id = str(uuid.uuid4())
    # Explicitly track in-memory model per constraints
    jobs[job_id] = {
        "status": "pending",
        "current_node": None,
        "iteration": 0,
        "result": None,
        "error": None,
    }
    
    background_tasks.add_task(_run_graph, job_id, source_code, file.filename)
    
    return {"job_id": job_id, "status": "processing"}


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Poll the status or final result of a job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobStatusResponse(job_id=job_id, **jobs[job_id])
