"""WebSocket endpoint for live preview."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.scene import SceneConfig
from ..rendering.scene_renderer import SceneRenderer

ws_router = APIRouter()
_renderer = SceneRenderer()


@ws_router.websocket("/ws/preview")
async def preview_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            try:
                config = SceneConfig(**data)
                svg_str = _renderer.render(config)
                await websocket.send_json({"status": "ok", "svg": svg_str})
            except Exception as e:
                await websocket.send_json({"status": "error", "message": str(e)})
    except WebSocketDisconnect:
        pass
