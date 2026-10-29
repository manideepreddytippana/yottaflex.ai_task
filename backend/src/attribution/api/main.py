"""FastAPI Application Entrypoint for Marketing Campaign Attribution & ROI System."""

from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.attribution.api.routes.attribution import router as attribution_router
from src.attribution.api.routes.campaigns import router as campaigns_router
from src.attribution.api.routes.contacts import router as contacts_router
from src.attribution.api.routes.exports import router as exports_router
from src.attribution.api.routes.health import router as health_router
from src.attribution.api.routes.issues import router as issues_router
from src.attribution.api.routes.metrics import router as metrics_router
from src.attribution.api.routes.runs import router as runs_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Marketing Campaign Attribution & ROI Analysis API",
        description=(
            "Deterministic synthetic data pipeline, customer journey reconstruction, "
            "multi-touch attribution comparison, financial reconciliation, and anomaly detection."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for local Vite dashboard frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(health_router)
    app.include_router(runs_router)
    app.include_router(campaigns_router)
    app.include_router(attribution_router)
    app.include_router(contacts_router)
    app.include_router(issues_router)
    app.include_router(metrics_router)
    app.include_router(exports_router)

    # Mount static dashboard if built
    if STATIC_DIR.is_dir() and (STATIC_DIR / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="static_assets")

        @app.get("/dashboard", tags=["Dashboard"])
        @app.get("/", tags=["Dashboard"])
        def serve_dashboard():
            return FileResponse(STATIC_DIR / "index.html")
    else:
        @app.get("/", tags=["Root"])
        def root():
            return {
                "name": "Marketing Campaign Attribution & ROI API",
                "version": "1.0.0",
                "docs": "/docs",
                "health": "/health",
            }

    return app


app = create_app()
