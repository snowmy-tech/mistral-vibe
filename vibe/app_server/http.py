from __future__ import annotations

from collections.abc import AsyncIterator
import json
from typing import Any

from starlette.websockets import WebSocket, WebSocketDisconnect

from vibe.app_server.transport import InvalidJsonRpcMessage, _decode_message


class WebSocketJsonRpcTransport:
    """WebSocket implementation of JsonRpcTransport for web/IDE client connections."""

    def __init__(self, websocket: WebSocket) -> None:
        self._websocket = websocket
        self._closed = False

    async def send(self, message: dict[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("WebSocket JSON-RPC transport is closed")
        data = json.dumps(message, separators=(",", ":"))
        await self._websocket.send_text(data)

    async def messages(self) -> AsyncIterator[dict[str, Any]]:
        try:
            while not self._closed:
                raw = await self._websocket.receive_text()
                yield _decode_message(raw)
        except WebSocketDisconnect:
            self._closed = True
        except Exception as exc:
            if not self._closed:
                self._closed = True
                raise InvalidJsonRpcMessage("Error receiving message over WebSocket") from exc

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._websocket.close()
        except Exception:
            pass
