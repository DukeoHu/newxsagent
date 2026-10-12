from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from xsagent import __version__
from xsagent.api.routes import (
    bible,
    chapters,
    explore,
    health,
    jobs,
    maintenance,
    onboarding,
    outlines,
    projects,
    settings,
    snapshots,
    supervision,
)
from xsagent.core.config import get_settings


def create_app() -> FastAPI:
    app_settings = get_settings()

    app = FastAPI(
        title="xsagent API",
        version=__version__,
        description="AI-assisted long-form novel writing system",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(bible.router)
    app.include_router(chapters.router)
    app.include_router(outlines.router)
    app.include_router(explore.router)
    app.include_router(jobs.router)
    app.include_router(maintenance.router)
    app.include_router(snapshots.router)
    app.include_router(supervision.router)
    app.include_router(onboarding.router)
    app.include_router(settings.router)

    return app
