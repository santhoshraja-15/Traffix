"""Tracks active WebSocket connections per simulation for broadcast fan-out."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, simulation_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[simulation_id].add(websocket)

    def disconnect(self, simulation_id: str, websocket: WebSocket) -> None:
        self._connections[simulation_id].discard(websocket)
        if not self._connections[simulation_id]:
            self._connections.pop(simulation_id, None)

    async def broadcast(self, simulation_id: str, message: dict) -> None:
        dead = []
        for ws in self._connections.get(simulation_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(simulation_id, ws)

    def connection_count(self, simulation_id: str) -> int:
        return len(self._connections.get(simulation_id, set()))


websocket_manager = WebSocketManager()
