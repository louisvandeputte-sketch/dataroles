"""FastAPI application for DataRoles admin panel."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pathlib import Path
from contextlib import asynccontextmanager
from loguru import logger

from web.api import queries, runs, jobs, quality, job_types, companies, tech_stack, locations, indeed_queries, indeed_runs, ranking
import asyncio

# Try to import background services - may fail if dependencies missing
try:
    from scheduler import get_scheduler
    SCHEDULER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Scheduler not available: {e}")
    SCHEDULER_AVAILABLE = False
    get_scheduler = None

try:
    from ingestion.auto_enrich_service import get_auto_enrich_service
    AUTO_ENRICH_AVAILABLE = True
except Exception as e:
    logger.warning(f"Auto-enrich service not available: {e}")
    AUTO_ENRICH_AVAILABLE = False
    get_auto_enrich_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup and shutdown)."""
    # Startup
    logger.info("🚀 Starting DataRoles application")
    
    # Check if we should start background services
    import os
    disable_background_services = os.getenv("DISABLE_BACKGROUND_SERVICES", "false").lower() == "true"
    
    scheduler = None
    auto_enrich_service = None
    auto_enrich_task = None
    
    # Start background services with error handling
    if not disable_background_services and (SCHEDULER_AVAILABLE or AUTO_ENRICH_AVAILABLE):
        logger.info("🔄 Starting background services...")
        try:
            # Start scheduler if available
            if SCHEDULER_AVAILABLE and get_scheduler:
                scheduler = get_scheduler()
                scheduler.start()
                logger.info("✅ Scheduler started")
            else:
                logger.warning("⏭️  Scheduler not available, skipping")
            
            # Start auto-enrichment service if available
            if AUTO_ENRICH_AVAILABLE and get_auto_enrich_service:
                auto_enrich_service = get_auto_enrich_service()
                auto_enrich_task = asyncio.create_task(auto_enrich_service.start())
                logger.info("✅ Auto-enrichment service started")
            else:
                logger.warning("⏭️  Auto-enrich service not available, skipping")
        except Exception as e:
            logger.error(f"⚠️ Failed to start background services: {e}")
            logger.error("App will continue without background services")
    else:
        if disable_background_services:
            logger.info("⏸️  Background services disabled via DISABLE_BACKGROUND_SERVICES")
        else:
            logger.info("⏸️  Background services not available")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DataRoles application")
    
    if not disable_background_services:
        # Stop auto-enrichment service
        if auto_enrich_service:
            auto_enrich_service.stop()
        if auto_enrich_task:
            auto_enrich_task.cancel()
            try:
                await auto_enrich_task
            except asyncio.CancelledError:
                pass
        logger.info("✅ Auto-enrichment service stopped")
        
        if scheduler:
            scheduler.shutdown()
            logger.info("✅ Scheduler stopped")
    else:
        logger.info("⏸️  Background services were disabled")


# Create FastAPI app
app = FastAPI(
    title="everyjob",
    description="Job aggregation platform admin panel",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False  # Disable automatic trailing slash redirects to prevent HTTP->HTTPS mixed content
)

# Add middleware to trust Railway's proxy headers
@app.middleware("http")
async def force_https_middleware(request: Request, call_next):
    """Force HTTPS scheme when behind Railway proxy."""
    # Railway sends X-Forwarded-Proto header
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto == "https":
        # Override the request URL scheme to HTTPS
        request.scope["scheme"] = "https"
    response = await call_next(request)
    return response

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

# Indeed API routers
app.include_router(indeed_queries.router, prefix="/api/indeed/queries", tags=["indeed-queries"])
app.include_router(indeed_runs.router, prefix="/api/indeed/runs", tags=["indeed-runs"])

# Ranking API router
app.include_router(ranking.router, prefix="/api/ranking", tags=["ranking"])


# Main pages
@app.get("/health")
async def health():
    """Health check endpoint for Railway."""
    return {"status": "healthy", "service": "dataroles"}


@app.get("/")
async def root(request: Request):
    """Root endpoint - redirect to queries page."""
    return templates.TemplateResponse("queries.html", {"request": request})


@app.get("/queries", response_class=HTMLResponse)
async def queries_page(request: Request):
    """Search queries management page."""
    return templates.TemplateResponse("queries.html", {"request": request})


@app.get("/runs", response_class=HTMLResponse)
async def runs_page(request: Request):
    """Scrape runs monitoring page."""
    return templates.TemplateResponse("runs.html", {"request": request})


@app.get("/indeed/queries", response_class=HTMLResponse)
async def indeed_queries_page(request: Request):
    """Indeed search queries management page."""
    return templates.TemplateResponse("indeed_queries.html", {"request": request})


@app.get("/indeed/runs", response_class=HTMLResponse)
async def indeed_runs_page(request: Request):
    """Indeed scrape runs monitoring page."""
    return templates.TemplateResponse("indeed_runs.html", {"request": request})


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
    return templates.TemplateResponse("companies_new.html", {"request": request})

@app.get("/companies-old", response_class=HTMLResponse)
async def companies_old_page(request: Request):
    """Old companies page (backup)."""
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
