from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from app.graph.workflow import research_workflow
from app.logging_config import logger
from app.config import settings
from app.tools.rate_limiter import rate_limiter

# FastAPI app
app = FastAPI(
    title="Multi-Agent AI Research System",
    description="Production-ready AI system with research, summarization, report writing, and fact checking agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ResearchRequest(BaseModel):
    topic: str
    max_retries: Optional[int] = 3

class ResearchResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    workflow_id: Optional[str]

# Global workflow state (in production, use Redis/Database)
workflow_state = {}

@app.get("/")
async def root():
    return {"message": "Multi-Agent AI Research System API"}

@app.post("/api/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start research workflow"""
    try:
        # Rate limiting
        await rate_limiter.check_limit()
        
        # Validate input
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic is required")
        
        if len(request.topic) > 500:
            raise HTTPException(status_code=400, detail="Topic too long")
        
        # Generate workflow ID
        import uuid
        workflow_id = str(uuid.uuid4())

        # Register workflow immediately so polling doesn't get 404 while background task starts
        workflow_state[workflow_id] = {
            "workflow_id": workflow_id,
            "topic": request.topic,
            "current_step": "research",
            "status": "running"
        }
        
        # Start workflow in background
        background_tasks.add_task(run_workflow, workflow_id, request.topic)
        
        return ResearchResponse(
            success=True,
            data={"workflow_id": workflow_id, "status": "started"},
            error=None,
            workflow_id=workflow_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/research/{workflow_id}")
async def get_research_result(workflow_id: str):
    """Get workflow result by ID"""
    if workflow_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    result = workflow_state[workflow_id]
    
    if "error" in result:
        return ResearchResponse(
            success=False,
            data=None,
            error=result["error"],
            workflow_id=workflow_id
        )
    
    return ResearchResponse(
        success=True,
        data=result,
        error=None,
        workflow_id=workflow_id
    )

@app.post("/api/generate-pdf/{workflow_id}")
async def generate_pdf(workflow_id: str):
    """Generate PDF for completed workflow"""
    if workflow_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    result = workflow_state[workflow_id]
    
    if not result.get("report_complete"):
        raise HTTPException(status_code=400, detail="Report not ready for PDF generation")
    
    try:
        from app.utils.pdf_generator import pdf_generator
        pdf_base64 = await pdf_generator.generate_pdf(result)
        return {
            "success": True,
            "pdf_data": pdf_base64,
            "mime_type": "application/pdf"
        }
    except OSError as e:
        logger.error("PDF native dependency missing", error=str(e))
        raise HTTPException(status_code=503, detail="PDF dependencies are not installed on this system")
    except Exception as e:
        logger.error("PDF generation API error", error=str(e))
        raise HTTPException(status_code=500, detail="PDF generation failed")

async def run_workflow(workflow_id: str, topic: str):
    """Run workflow and store result"""
    try:
        logger.info("Starting workflow", workflow_id=workflow_id, topic=topic)
        
        result = await research_workflow.run(topic)

        # Store result
        if isinstance(result, dict):
            result.setdefault("workflow_id", workflow_id)
            result.setdefault("topic", topic)
        workflow_state[workflow_id] = result
        
        logger.info("Workflow completed", 
                   workflow_id=workflow_id, 
                   success=result.get("current_step") == "complete")
                   
    except Exception as e:
        logger.error("Workflow execution failed", workflow_id=workflow_id, error=str(e))
        workflow_state[workflow_id] = {
            "error": str(e),
            "success": False
        }

@app.on_event("startup")
async def startup_event():
    logger.info("Multi-Agent AI System starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Multi-Agent AI System shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
