"""FastAPI application for DataRoles admin panel."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from contextlib import asynccontextmanager
from loguru import logger

from web.api import queries, runs, jobs, quality, job_types, companies, tech_stack, locations
from scheduler import get_scheduler
from ingestion.auto_enrich_service import get_auto_enrich_service
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup and shutdown)."""
    # Startup
    logger.info("🚀 Starting DataRoles application")
    
    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("✅ Scheduler started")
    
    # Start auto-enrichment service
    auto_enrich_service = get_auto_enrich_service()
    auto_enrich_task = asyncio.create_task(auto_enrich_service.start())
    logger.info("✅ Auto-enrichment service started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DataRoles application")
    
    # Stop auto-enrichment service
    auto_enrich_service.stop()
    auto_enrich_task.cancel()
    try:
        await auto_enrich_task
    except asyncio.CancelledError:
        pass
    logger.info("✅ Auto-enrichment service stopped")
    
    scheduler.shutdown()
    logger.info("✅ Scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="DataRoles Admin",
    description="Job aggregation platform admin panel",
    version="1.0.0",
    lifespan=lifespan
)


# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log and return detailed validation errors."""
    errors = exc.errors()
    body = await request.body()
    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Request body: {body.decode('utf-8')}")
    logger.error(f"Validation errors: {errors}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "body": body.decode('utf-8')
        }
    )

# Setup templates
templates = Jinja2Templates(directory="web/templates")

# Setup static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Include API routers
app.include_router(queries.router, prefix="/api/queries", tags=["queries"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(quality.router, prefix="/api/quality", tags=["quality"])
app.include_router(job_types.router, prefix="/api/job-types", tags=["job-types"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(tech_stack.router, prefix="/api/tech-stack", tags=["tech-stack"])
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])


# Main pages
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Redirect to queries page."""
    return templates.TemplateResponse("queries.html", {"request": request})


@app.get("/queries", response_class=HTMLResponse)
async def queries_page(request: Request):
    """Search queries management page."""
    return templates.TemplateResponse("queries.html", {"request": request})


@app.get("/runs", response_class=HTMLResponse)
async def runs_page(request: Request):
    """Scrape runs monitoring page."""
    return templates.TemplateResponse("runs.html", {"request": request})


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """Job database page."""
    return templates.TemplateResponse("jobs.html", {"request": request})


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail_page(request: Request, job_id: str):
    """Job detail page."""
    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "job_id": job_id
    })


@app.get("/quality", response_class=HTMLResponse)
async def quality_page(request: Request):
    """Data quality tools page."""
    return templates.TemplateResponse("quality.html", {"request": request})


@app.get("/job-types", response_class=HTMLResponse)
async def job_types_page(request: Request):
    """Job types management page."""
    return templates.TemplateResponse("job_types.html", {"request": request})


@app.get("/companies", response_class=HTMLResponse)
async def companies_page(request: Request):
    """Companies master data management page."""
    return templates.TemplateResponse("companies.html", {"request": request})


@app.get("/tech-stack", response_class=HTMLResponse)
async def tech_stack_page(request: Request):
    """Tech stack masterdata management page."""
    return templates.TemplateResponse("tech_stack.html", {"request": request})


@app.get("/locations", response_class=HTMLResponse)
async def locations_page(request: Request):
    """Locations master data management page."""
    return templates.TemplateResponse("locations.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
