from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from vibe.app_server.web import create_app

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def test_client() -> Iterator[TestClient]:
    app = create_app(experimental_harness=False)
    with TestClient(app) as client:
        yield client


def test_health_check_endpoint(test_client: TestClient) -> None:
    response = test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mistral-vibe-web-server"
    assert "vibe" in data["partitions"]


def test_homepage_html_rendering(test_client: TestClient) -> None:
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Mistral Vibe - Web Cloud" in response.text
    assert "--mistral-orange: #FF7000;" in response.text
    assert "Studio: Agents & Connectors" in response.text


def test_websocket_jsonrpc_handshake(test_client: TestClient) -> None:
    with test_client.websocket_connect("/ws") as websocket:
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {"name": "test_web_client", "version": "1.0.0"},
                "capabilities": {},
            },
        }
        websocket.send_text(json.dumps(init_request))
        data = websocket.receive_text()
        response = json.loads(data)
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "vibe-app-server"
