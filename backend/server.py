"""
FastAPI server exposing the LegacyLens pipeline via LangGraph.

Phase 4: Jobs persisted in SQLite, artifacts served from run-history
directories, CORS enabled for the Next.js frontend.
"""

import uuid
import warnings
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

# Suppress Pydantic / Langchain warnings for cleaner output
warnings.filterwarnings("ignore", message=".*Pydantic V1.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", module="langchain")

from backend.state import PipelineState
from backend.graph import build_pipeline_graph
from backend.analyst import AnalystAgent
from backend.coder import CoderAgent
from backend.reviewer import ReviewerAgent
from backend.provider import MockProvider
from backend.contracts import PipelineError
from backend import db


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="LegacyLens Pipeline API", version="2.0.0")

# CORS — allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class JobStatusResponse(BaseModel):
    """Data contract for polling job status and retrieving results.

    Status values:
      - "pending"              — job accepted, not yet started
      - "processing"           — pipeline is running
      - "completed"            — pipeline finished without errors
      - "completed_with_errors"— pipeline produced partial results with errors
      - "failed"               — pipeline could not produce any result
    """
    job_id: str
    file_name: str = ""
    source_code: str = ""
    status: str
    current_node: str | None = None
    iteration: int = 0
    result: dict | None = None
    error: str | None = None
    errors: list[PipelineError] = Field(default_factory=list)


class JobSummary(BaseModel):
    """Lightweight job info for the job list — no full result blob."""
    job_id: str
    file_name: str
    status: str
    confidence_level: str | None = None
    iterations: int = 0
    has_errors: bool = False
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    """Paginated job list response."""
    jobs: list[JobSummary]
    total: int
    page: int
    limit: int
    total_pages: int


# ---------------------------------------------------------------------------
# Agent / graph setup
# ---------------------------------------------------------------------------

# Initialize agents with MockProvider for Phase 4 dev
provider = MockProvider()
analyst = AnalystAgent(provider)
coder = CoderAgent(provider)
reviewer = ReviewerAgent(provider)

# Compile LangGraph execution graph once
pipeline_graph = build_pipeline_graph(analyst, coder, reviewer)

# Ensure DB schema exists on import
db.init_db()


# ---------------------------------------------------------------------------
# Content-type mapping for artifacts
# ---------------------------------------------------------------------------

_CONTENT_TYPES: dict[str, str] = {
    ".json": "application/json",
    ".py": "text/x-python",
    ".md": "text/markdown",
}


# ---------------------------------------------------------------------------
# Background pipeline runner
# ---------------------------------------------------------------------------

def _run_graph(job_id: str, source_code: str, file_name: str, dependencies_dict: dict[str, str] | None = None) -> None:
    """Executes the LangGraph pipeline in the background, persisting to DB."""
    db.update_job(job_id, status="processing")

    deps = dependencies_dict if dependencies_dict else {}
    initial_state = PipelineState(
        source_code=source_code,
        file_name=file_name,
        logic_map=None,
        coder_output=None,
        reviewer_output=None,
        result=None,
        iterations=0,
        error=None,
        errors=[],
        dependencies_dict=deps,
    )

    try:
        for event in pipeline_graph.stream(initial_state):
            for node_name, state_update in event.items():
                db.update_job(job_id, current_node=node_name)

                if "iterations" in state_update:
                    db.update_job(job_id, iteration=state_update["iterations"])

                # Analyst failure — no result possible
                if "error" in state_update and state_update["error"]:
                    db.update_job(
                        job_id,
                        status="failed",
                        error=state_update["error"],
                    )
                    return

                # Finalize node produced a result
                if "result" in state_update and state_update["result"] is not None:
                    result_obj = state_update["result"]
                    result_dict = result_obj.model_dump()
                    pipeline_errors = result_obj.errors

                    status = "completed_with_errors" if pipeline_errors else "completed"

                    # Persist artifacts to filesystem
                    from backend.pipeline import save_run_history
                    run_dir = save_run_history(result_obj, base_dir="runs", job_id=job_id)

                    # Persist to DB
                    db.update_job(job_id, status=status, run_dir=str(run_dir))
                    db.save_pipeline_result(job_id, result_dict)

    except Exception as e:
        db.update_job(
            job_id,
            status="failed",
            error=f"Graph execution crashed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/jobs", tags=["Jobs"])
def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dependencies: list[UploadFile] = File(default=[])
) -> dict[str, str]:
    """Submit a primary COBOL file and optional dependencies to spawn a metadata job."""
    content = file.file.read()
    source_code = content.decode("utf-8", errors="replace")
    
    dependencies_dict = {}
    submitted_files = [file.filename or "unknown.cbl"]
    
    # Process optional dependencies recursively without blowing up backwards compatibility
    if dependencies and len(dependencies) > 0:
        for dep in dependencies:
            if not dep or not dep.filename:
                continue
            dep_content = dep.file.read()
            # File(...) can return a single object with no filename if empty payload mapping happens in some clients
            if dep.filename:
                dependencies_dict[dep.filename] = dep_content.decode("utf-8", errors="replace")
                submitted_files.append(dep.filename)

    job_id = str(uuid.uuid4())
    db.create_job(job_id, file.filename or "unknown.cbl", source_code, submitted_files)

    background_tasks.add_task(_run_graph, job_id, source_code, file.filename or "unknown.cbl", dependencies_dict)

    return {"job_id": job_id, "status": "processing"}


@app.get("/api/v1/jobs", response_model=JobListResponse, tags=["Jobs"])
def list_jobs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> JobListResponse:
    """List all jobs, paginated, newest-first."""
    data = db.list_jobs(page=page, limit=limit)
    return JobListResponse(
        jobs=[JobSummary(**j) for j in data["jobs"]],
        total=data["total"],
        page=data["page"],
        limit=data["limit"],
        total_pages=data["total_pages"],
    )


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
def get_job_status(job_id: str) -> JobStatusResponse:
    """Poll the status or full result of a job."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch full result from DB if available
    result = db.get_pipeline_result(job_id)

    # Reconstruct errors list from result
    errors: list[PipelineError] = []
    if result and result.get("errors"):
        for e in result["errors"]:
            errors.append(PipelineError(**e))

    return JobStatusResponse(
        job_id=job["id"],
        file_name=job["file_name"],
        source_code=job["source_code"],
        status=job["status"],
        current_node=job.get("current_node"),
        iteration=job.get("iteration", 0),
        result=result,
        error=job.get("error"),
        errors=errors,
    )


@app.get("/api/v1/jobs/{job_id}/artifacts/{name}", tags=["Artifacts"])
def get_artifact(job_id: str, name: str):
    """Retrieve a specific artifact file from a job's run history.

    Only filenames in the allowlist may be requested.  Path traversal
    is blocked by both the allowlist check and an independent separator check.
    """
    # Security: reject path separators (defense-in-depth)
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid artifact name")

    # Security: allowlist check
    if name not in db.ALLOWED_ARTIFACTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown artifact '{name}'. Allowed: {sorted(db.ALLOWED_ARTIFACTS)}",
        )

    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    run_dir = job.get("run_dir")
    if not run_dir:
        raise HTTPException(
            status_code=409,
            detail="Job has not completed yet; no artifacts available",
        )

    artifact_path = Path(run_dir) / name
    if not artifact_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Artifact '{name}' not available for this job. "
                "The corresponding pipeline stage may not have completed."
            ),
        )

    content = artifact_path.read_text(encoding="utf-8")
    suffix = artifact_path.suffix
    content_type = _CONTENT_TYPES.get(suffix, "text/plain")

    if content_type == "application/json":
        return JSONResponse(content=json.loads(content) if content.strip() else {})

    return PlainTextResponse(content=content, media_type=content_type)


# Need json import for artifact endpoint
import json
