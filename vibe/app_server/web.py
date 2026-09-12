from __future__ import annotations

import argparse

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket
import uvicorn

from vibe._experimental_harness import add_experimental_harness_argument
from vibe.app_server._runtime import HarnessProcess, create_harness_server
from vibe.app_server.http import WebSocketJsonRpcTransport
from vibe.core.config import load_dotenv_values
from vibe.core.config.harness_files import init_harness_files_manager
from vibe.core.paths import LOG_FILE
from vibe.observability.logging import init_file_logging, logger

# Single process instance to share across web connections
_global_harness_process: HarnessProcess | None = None


def get_harness_process(experimental_harness: bool = False) -> HarnessProcess:
    global _global_harness_process
    if _global_harness_process is None:
        _global_harness_process = HarnessProcess(
            experimental_harness=experimental_harness
        )
    return _global_harness_process


# --- Brand HTML Template containing Mistral AI Design System & Theme ---
MISTRAL_WEB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mistral Vibe - Web Cloud</title>
    <style>
        :root {
            --mistral-orange: #FF7000;
            --mistral-orange-hover: #E06200;
            --mistral-black: #0F0F0F;
            --mistral-card-bg: #1A1A1A;
            --mistral-sidebar-bg: #141414;
            --mistral-border: #2A2A2A;
            --mistral-text: #EAEAEA;
            --mistral-muted: #888888;
            --mistral-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --mistral-code-font: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--mistral-black);
            color: var(--mistral-text);
            font-family: var(--mistral-font);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        /* Sidebar Navigation */
        .sidebar {
            width: 240px;
            background-color: var(--mistral-sidebar-bg);
            border-right: 1px solid var(--mistral-border);
            display: flex;
            flex-direction: column;
            padding: 20px 0;
        }

        .brand-header {
            padding: 0 20px 20px;
            border-bottom: 1px solid var(--mistral-border);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo {
            width: 28px;
            height: 28px;
            background: var(--mistral-orange);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: black;
            font-size: 16px;
        }

        .brand-title {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .nav-section {
            padding: 20px 10px;
            flex-grow: 1;
        }

        .nav-label {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--mistral-muted);
            letter-spacing: 1px;
            padding: 0 10px 8px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 6px;
            color: var(--mistral-text);
            text-decoration: none;
            font-size: 14px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: background 0.15s ease;
        }

        .nav-item:hover, .nav-item.active {
            background: #242424;
            color: var(--mistral-orange);
        }

        .nav-item .icon {
            font-size: 16px;
        }

        /* Main Workspace */
        .main-content {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            background-color: var(--mistral-black);
            position: relative;
        }

        .top-bar {
            height: 56px;
            border-bottom: 1px solid var(--mistral-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            background: var(--mistral-sidebar-bg);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--mistral-muted);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #10B981;
            border-radius: 50%;
        }

        /* Views */
        .view-panel {
            display: none;
            flex-grow: 1;
            padding: 24px;
            overflow-y: auto;
        }

        .view-panel.active {
            display: flex;
            flex-direction: column;
        }

        /* Vibe View */
        .chat-container {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
        }

        .chat-messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 16px 0;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            padding: 16px;
            border-radius: 8px;
            background: var(--mistral-card-bg);
            border: 1px solid var(--mistral-border);
            font-size: 14px;
            line-height: 1.6;
        }

        .message.assistant {
            border-left: 3px solid var(--mistral-orange);
        }

        .input-box-container {
            padding-top: 16px;
            position: sticky;
            bottom: 0;
            background: var(--mistral-black);
        }

        .chat-input {
            width: 100%;
            padding: 14px 16px;
            background: var(--mistral-card-bg);
            border: 1px solid var(--mistral-border);
            border-radius: 8px;
            color: var(--mistral-text);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: var(--mistral-orange);
        }

        /* Cards Grid for Studio / Admin */
        .grid-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .card {
            background: var(--mistral-card-bg);
            border: 1px solid var(--mistral-border);
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }

        .card:hover {
            border-color: var(--mistral-orange);
            transform: translateY(-2px);
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--mistral-orange);
        }

        .card-desc {
            font-size: 13px;
            color: var(--mistral-muted);
            line-height: 1.4;
        }

        .btn {
            background: var(--mistral-orange);
            color: black;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
            display: inline-block;
        }

        .btn:hover {
            background: var(--mistral-orange-hover);
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="brand-header">
            <div class="brand-logo">M</div>
            <div class="brand-title">Mistral Vibe</div>
        </div>

        <div class="nav-section">
            <div class="nav-label">Vibe Space</div>
            <div class="nav-item active" onclick="switchTab('vibe')">
                <span class="icon">💬</span>
                <span>Chat & Code</span>
            </div>
            <div class="nav-item" onclick="switchTab('work')">
                <span class="icon">⚡</span>
                <span>Work / Tasks</span>
            </div>

            <div class="nav-label" style="margin-top: 16px;">Studio</div>
            <div class="nav-item" onclick="switchTab('studio')">
                <span class="icon">🤖</span>
                <span>Agents & Connectors</span>
            </div>

            <div class="nav-label" style="margin-top: 16px;">Admin</div>
            <div class="nav-item" onclick="switchTab('admin')">
                <span class="icon">⚙️</span>
                <span>Governance & Config</span>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="top-bar">
            <h2 id="page-title" style="font-size: 16px; font-weight: 600;">Vibe: Chat & Code</h2>
            <div class="status-badge">
                <div class="status-dot"></div>
                <span id="ws-status">Connected to Web Cloud RPC</span>
            </div>
        </div>

        <!-- Vibe Partition -->
        <div id="vibe-panel" class="view-panel active">
            <div class="chat-container">
                <div class="chat-messages" id="chat-messages">
                    <div class="message assistant">
                        <strong>Mistral Vibe Assistant:</strong><br>
                        Welcome to Mistral Vibe Web Cloud. I am connected directly to your Vibe App Server RPC backend.
                    </div>
                </div>
                <div class="input-box-container">
                    <input type="text" id="user-input" class="chat-input" placeholder="Ask Vibe to write code, inspect files, or run tasks..." onkeydown="handleInputKey(event)">
                </div>
            </div>
        </div>

        <!-- Work Partition -->
        <div id="work-panel" class="view-panel">
            <h3>Work & Task Management</h3>
            <p style="color: var(--mistral-muted); margin-top: 8px;">Active workflows, subagents, and background execution tasks.</p>
            <div class="grid-cards">
                <div class="card">
                    <div class="card-title">Code Exploration</div>
                    <div class="card-desc">Subagent analyzing codebase architecture and symbol dependencies.</div>
                    <button class="btn">View Task</button>
                </div>
                <div class="card">
                    <div class="card-title">Refactoring Loop</div>
                    <div class="card-desc">Iterative edits and tests validation cycle.</div>
                    <button class="btn">View Progress</button>
                </div>
            </div>
        </div>

        <!-- Studio Partition -->
        <div id="studio-panel" class="view-panel">
            <h3>Studio: Agent Creation & Connectors</h3>
            <p style="color: var(--mistral-muted); margin-top: 8px;">Manage agent profiles, MCP tools, and external workspace connectors.</p>
            <div class="grid-cards">
                <div class="card">
                    <div class="card-title">Ask Agent</div>
                    <div class="card-desc">Interactive profile requiring approval for tool executions.</div>
                </div>
                <div class="card">
                    <div class="card-title">Plan Agent</div>
                    <div class="card-desc">Read-only agent for exploration and planning.</div>
                </div>
                <div class="card">
                    <div class="card-title">MCP Connectors</div>
                    <div class="card-desc">Streamable HTTP / stdio MCP servers and tools integration.</div>
                </div>
            </div>
        </div>

        <!-- Admin Partition -->
        <div id="admin-panel" class="view-panel">
            <h3>Admin: Governance & Permissions</h3>
            <p style="color: var(--mistral-muted); margin-top: 8px;">System trust store, security boundaries, and telemetry options.</p>
            <div class="grid-cards">
                <div class="card">
                    <div class="card-title">Trust Folder System</div>
                    <div class="card-desc">Manage trusted directories and file access permissions.</div>
                </div>
                <div class="card">
                    <div class="card-title">Telemetry & OTLP</div>
                    <div class="card-desc">OpenTelemetry tracing and redaction controls.</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const wsUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws';
        let ws;

        function connectWebSocket() {
            ws = new WebSocket(wsUrl);
            ws.onopen = () => {
                document.getElementById('ws-status').innerText = 'Connected (RPC Ready)';
                // Send JSON-RPC initialize request
                const initReq = {
                    jsonrpc: "2.0",
                    id: 1,
                    method: "initialize",
                    params: {
                        clientInfo: { name: "vibe_web_cloud", version: "2.25.0" },
                        capabilities: {}
                    }
                };
                ws.send(JSON.stringify(initReq));
            };
            ws.onclose = () => {
                document.getElementById('ws-status').innerText = 'Disconnected';
                setTimeout(connectWebSocket, 3000);
            };
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.method === 'turn/completed' || data.result) {
                    // Handle incoming messages/responses
                }
            };
        }

        connectWebSocket();

        function switchTab(tab) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.view-panel').forEach(el => el.classList.remove('active'));

            const titles = {
                vibe: 'Vibe: Chat & Code',
                work: 'Vibe: Work & Tasks',
                studio: 'Studio: Agents & Connectors',
                admin: 'Admin: Governance'
            };

            document.getElementById('page-title').innerText = titles[tab];

            if (tab === 'vibe' || tab === 'work') {
                document.getElementById(tab + '-panel').classList.add('active');
            } else {
                document.getElementById(tab + '-panel').classList.add('active');
            }
        }

        function handleInputKey(event) {
            if (event.key === 'Enter') {
                const input = document.getElementById('user-input');
                const text = input.value.trim();
                if (!text) return;

                const messages = document.getElementById('chat-messages');
                const userMsg = document.createElement('div');
                userMsg.className = 'message';
                userMsg.innerHTML = `<strong>You:</strong><br>${text}`;
                messages.appendChild(userMsg);

                input.value = '';
                messages.scrollTop = messages.scrollHeight;
            }
        }
    </script>
</body>
</html>
"""


async def homepage(request: Request) -> HTMLResponse:
    """Serve the 1:1 Mistral Web Cloud interface."""
    return HTMLResponse(MISTRAL_WEB_HTML)


async def api_health(request: Request) -> JSONResponse:
    """Health check endpoint for cloud/load balancer probes."""
    return JSONResponse({
        "status": "ok",
        "service": "mistral-vibe-web-server",
        "partitions": ["vibe", "studio", "admin"],
    })


async def websocket_endpoint(websocket: WebSocket) -> None:
    """JSON-RPC over WebSocket endpoint for Vibe CLI, IDE extensions, and Web UI."""
    await websocket.accept()
    transport = WebSocketJsonRpcTransport(websocket)
    process = get_harness_process()
    server = await create_harness_server(
        transport,
        transport_kind="in_process",
        process=process,
    )
    try:
        await server.serve()
    except Exception as exc:
        logger.warning("WebSocket RPC server session finished/closed: %s", exc)


def create_app(experimental_harness: bool = False) -> Starlette:
    get_harness_process(experimental_harness=experimental_harness)
    routes = [
        Route("/", homepage),
        Route("/api/health", api_health),
        WebSocketRoute("/ws", websocket_endpoint),
        WebSocketRoute("/v1/ws", websocket_endpoint),
    ]
    return Starlette(debug=False, routes=routes)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Mistral Vibe Web App Server")
    add_experimental_harness_argument(parser)
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    init_harness_files_manager("user", "project")
    init_file_logging(LOG_FILE.path)
    load_dotenv_values()

    app = create_app(experimental_harness=args.experimental_harness)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
