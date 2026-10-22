"""FastAPI application for DP1 traffic signal optimization simulator."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .routes import experiments, health, runs, site_model

app = FastAPI(
    title="DP1 Traffic Signal Optimizer API",
    description="Thin adapter over SUMO simulation engine, research experiments, and live telemetry.",
    version="1.0.0",
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes under /api
app.include_router(health.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(site_model.router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "DP1 Traffic Signal Optimizer API",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "summary_url": "/api/summary",
    }
