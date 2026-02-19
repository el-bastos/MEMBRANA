"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from .websocket import ws_router


def create_app() -> FastAPI:
    app = FastAPI(title="Membrana", version="0.2.0")

    # Static files
    static_dir = Path(__file__).resolve().parent.parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # REST routes
    app.include_router(router, prefix="/api")

    # WebSocket routes
    app.include_router(ws_router)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = static_dir / "index.html"
        return index_path.read_text()

    return app
