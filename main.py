from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
import uuid
import logging
from datetime import datetime
import time

# Import our custom modules
from research import ResearchEngine
from models import ResearchJob, ResearchRequest, ResearchResults, Subcontractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Subcontractor Research API",
    description="API for discovering and ranking subcontractors based on criteria",
    version="1.0.0"
)

# In-memory storage for jobs (in production, use a database)
jobs_store: Dict[str, Any] = {}

class JobRequest(BaseModel):
    trade: str = Field(..., description="Trade type to search (e.g. electrical, plumbing)")
    city: str = Field(..., description="City of the project")
    state: str = Field(..., description="U.S. State (2-letter code)")
    min_bond: int = Field(..., description="Minimum bonding capacity required")
    keywords: List[str] = Field(default=[], description="Optional context keywords")

class JobResponse(BaseModel):
    job_id: str
    status: str

@app.post("/research-jobs", response_model=JobResponse)
async def create_research_job(request: JobRequest, background_tasks: BackgroundTasks):
    """Create a new subcontractor research job"""
    job_id = str(uuid.uuid4())
    
    # Initialize job in our store
    jobs_store[job_id] = {
        "status": "QUEUED",
        "request": request.dict(),
        "created_at": datetime.now().isoformat(),
        "results": None
    }
    
    # Add the research task to run in the background
    background_tasks.add_task(
        process_research_job, 
        job_id, 
        request.trade, 
        request.city, 
        request.state, 
        request.min_bond, 
        request.keywords
    )
    
    return JobResponse(job_id=job_id, status="QUEUED")

async def process_research_job(job_id: str, trade: str, city: str, state: str, min_bond: int, keywords: List[str]):
    """Process a research job in the background"""
    try:
        # Update job status
        jobs_store[job_id]["status"] = "PROCESSING"
        
        # Initialize the research engine
        engine = ResearchEngine()
        
        # Run the research pipeline
        logger.info(f"Starting research for job {job_id}")
        results = await engine.run_research(trade, city, state, min_bond, keywords)
        
        # Update job with results
        jobs_store[job_id]["status"] = "SUCCEEDED"
        jobs_store[job_id]["results"] = results
        jobs_store[job_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Research job {job_id} completed successfully")
    except Exception as e:
        # Handle errors
        logger.error(f"Error processing job {job_id}: {str(e)}")
        jobs_store[job_id]["status"] = "FAILED"
        jobs_store[job_id]["error"] = str(e)

@app.get("/research-jobs/{job_id}")
async def get_research_results(job_id: str):
    """Get the results of a research job"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_store[job_id]
    
    # Return different response based on job status
    if job["status"] == "QUEUED":
        return {"status": "QUEUED", "message": "Job is queued for processing"}
    elif job["status"] == "PROCESSING":
        return {"status": "PROCESSING", "message": "Job is currently being processed"}
    elif job["status"] == "FAILED":
        return {"status": "FAILED", "message": f"Job processing failed: {job.get('error', 'Unknown error')}"}
    elif job["status"] == "SUCCEEDED":
        return {
            "status": "SUCCEEDED",
            "results": job["results"]
        }

@app.get("/")
async def root():
    """API root - health check"""
    return {"status": "online", "message": "Subcontractor Research API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
