"""WenNian FastAPI application.

Provides REST API endpoints for health checks and aging assessments.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.core.config import load_config
from src.core.logging import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize configuration and logging on startup."""
    try:
        config = load_config()
        setup_logging(config)
        logger.info("WenNian API v2.0.0 started")
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
    yield


app = FastAPI(
    title="问年 WenNian API",
    description="十二维度衰老元模型与工业决策引擎 API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (reports, images)
static_dir = Path(__file__).parent.parent.parent / "data"
static_dir.mkdir(parents=True, exist_ok=True)
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/api/v1/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        JSON with status and version.
    """
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/v1/evaluate")
async def evaluate_aging(payload: Dict[str, Any]) -> JSONResponse:
    """Evaluate biological age from biomarker data.

    Args:
        payload: JSON body with 'biomarkers' dictionary containing
                 age and blood chemistry values.

    Returns:
        JSON with biological age assessment results.
    """
    from src.validation.input_validator import InputValidator
    from src.clocks import ClockRegistry
    from src.clocks.phenoage import PhenoAgeClock
    from src.clocks.kdm import KDMClock
    from src.clocks.dnn import DNNClock
    from src.clocks.lifeclock import LifeClock
    from src.integrator import AgingIntegrator
    from src.outputs.report_builder import build_markdown_report
    from src.agents.auditor import Auditor

    biomarkers = payload.get("biomarkers", {})
    if not biomarkers:
        raise HTTPException(status_code=400, detail="No biomarkers provided")

    validator = InputValidator()
    validation = validator.validate(biomarkers)
    if not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail={"errors": validation.errors, "warnings": validation.warnings},
        )

    registry = ClockRegistry()
    registry.clear()
    registry.register(phenoage=PhenoAgeClock())
    registry.register(kdm=KDMClock())
    registry.register(dnn=DNNClock())
    registry.register(lifeclock=LifeClock())

    integrator = AgingIntegrator(registry=registry)
    result = integrator.assess(biomarkers)

    report_text = build_markdown_report(result)

    auditor = Auditor()
    audit_output = auditor.execute({
        "report_text": report_text,
        "biological_age": result.biological_age,
        "chronological_age": result.chronological_age,
    })

    return JSONResponse(content={
        "biological_age": result.biological_age,
        "chronological_age": result.chronological_age,
        "age_acceleration": result.age_acceleration,
        "confidence": result.confidence,
        "lower_bound": result.lower_bound,
        "upper_bound": result.upper_bound,
        "clock_results": [
            {"name": c.clock_name, "age": c.predicted_age, "confidence": c.confidence, "status": c.status}
            for c in result.clock_results
        ],
        "warnings": validation.warnings + result.warnings,
        "audit": audit_output.data,
    })