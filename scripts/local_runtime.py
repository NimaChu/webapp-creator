#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import threading
import urllib.error
import urllib.request
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


MAX_REQUEST_BYTES = 24 * 1024 * 1024
DEFAULT_CONFIG_NAME = ".webapp.local.json"


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def _load_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read runtime config: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Runtime config must be a JSON object.")
    if _contains_forbidden_secret(data):
        raise ValueError(
            "Do not store credentials in the runtime config. "
            "Use apiKeyEnv and set the named environment variable instead."
        )
    return data


def _contains_forbidden_secret(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in {"apikey", "token", "secret", "password", "authorization"}:
                if normalized != "apikeyenv":
                    return True
            if _contains_forbidden_secret(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_secret(item) for item in value)
    return False


def _profile(config: dict[str, Any], name: str) -> dict[str, Any]:
    raw = config.get(name)
    if isinstance(raw, dict):
        return raw
    if name == "chat" and all(key in config for key in ("baseUrl", "model")):
        return config
    return {}


def _endpoint(profile: dict[str, Any], suffix: str) -> str:
    base_url = str(profile.get("baseUrl", "")).strip().rstrip("/")
    if not base_url:
        raise ValueError("The selected runtime profile has no baseUrl.")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("baseUrl must begin with http:// or https://.")
    return f"{base_url}/{suffix.lstrip('/')}"


class RuntimeHandler(SimpleHTTPRequestHandler):
    server_version = "WebAppLocalRuntime/1.0"

    def __init__(
        self,
        *args: object,
        directory: str,
        runtime_config: dict[str, Any],
        **kwargs: object,
    ) -> None:
        self.runtime_config = runtime_config
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format: str, *args: object) -> None:
        message = format % args
        if "/runtime/ai/" not in message:
            super().log_message("%s", message)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/runtime/health":
            chat = _profile(self.runtime_config, "chat")
            image = _profile(self.runtime_config, "image")
            self._send_json(
                200,
                {
                    "ok": True,
                    "chat": {
                        "configured": bool(chat.get("baseUrl") and chat.get("model")),
                        "model": chat.get("model", ""),
                    },
                    "image": {
                        "configured": bool(image.get("baseUrl") and image.get("model")),
                        "model": image.get("model", ""),
                    },
                },
            )
            return
        super().do_GET()

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
        if route not in {"/runtime/ai/chat", "/runtime/ai/image"}:
            self._send_json(404, {"error": "Unknown runtime route."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length."})
            return
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request body is empty or too large."})
            return

        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Request body must be a JSON object."})
            return

        profile_name = "chat" if route.endswith("/chat") else "image"
        suffix = "chat/completions" if profile_name == "chat" else "images/generations"
        try:
            profile = _profile(self.runtime_config, profile_name)
            if not profile:
                raise ValueError(
                    f"No {profile_name} runtime is configured. "
                    f"Create {DEFAULT_CONFIG_NAME} from the example file."
                )
            endpoint = _endpoint(profile, suffix)
            forwarded = dict(payload)
            forwarded.setdefault("model", profile.get("model"))
            if profile_name == "chat" and not isinstance(forwarded.get("messages"), list):
                raise ValueError("Chat requests require a messages array.")
            if profile_name == "image" and not str(forwarded.get("prompt", "")).strip():
                raise ValueError("Image requests require a prompt.")
            self._forward(endpoint, profile, forwarded)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})

    def _forward(
        self,
        endpoint: str,
        profile: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json",
        }
        env_name = str(profile.get("apiKeyEnv", "")).strip()
        if env_name:
            api_key = os.environ.get(env_name, "")
            if not api_key:
                self._send_json(
                    503,
                    {"error": f"Environment variable {env_name} is not set."},
                )
                return
            headers["Authorization"] = f"Bearer {api_key}"

        timeout = float(profile.get("timeoutSeconds", 120))
        request = urllib.request.Request(
            endpoint,
            data=_json_bytes(payload),
            headers=headers,
            method="POST",
        )
        parsed_endpoint = urlparse(endpoint)
        if parsed_endpoint.hostname in {"127.0.0.1", "localhost", "::1"}:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        else:
            opener = urllib.request.build_opener()
        try:
            with opener.open(request, timeout=timeout) as response:
                content_type = response.headers.get(
                    "Content-Type", "application/json; charset=utf-8"
                )
                self.send_response(response.status)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                while chunk := response.read(8192):
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as exc:
            body = exc.read()
            self.send_response(exc.code)
            self.send_header(
                "Content-Type",
                exc.headers.get("Content-Type", "application/json; charset=utf-8"),
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body or _json_bytes({"error": str(exc)}))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            self._send_json(502, {"error": f"Could not reach the configured model: {exc}"})

    def _send_json(self, status: int, payload: object) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def _available_port(host: str, preferred: int) -> int:
    if preferred == 0:
        return 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if probe.connect_ex((host, preferred)) != 0:
            return preferred
    return 0


def run_server(
    root: Path,
    *,
    config_path: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 4327,
    open_browser: bool = False,
) -> None:
    root = root.expanduser().resolve()
    if root.is_file():
        root = root.parent
    if not (root / "index.html").is_file():
        raise SystemExit(f"Could not find index.html under {root}")

    resolved_config = (
        config_path.expanduser().resolve()
        if config_path
        else root / DEFAULT_CONFIG_NAME
    )
    try:
        config = _load_config(resolved_config)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    handler = partial(
        RuntimeHandler,
        directory=str(root),
        runtime_config=config,
    )
    selected_port = _available_port(host, port)
    server = ThreadingHTTPServer((host, selected_port), handler)
    actual_port = server.server_address[1]
    url = f"http://{host}:{actual_port}/"
    print(f"Serving: {root}")
    print(f"URL: {url}")
    if config:
        print(f"Runtime config: {resolved_config}")
    else:
        print("Runtime config: none (static mode)")
    if open_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve a standalone web app with an optional local model proxy."
    )
    parser.add_argument("project")
    parser.add_argument("--config")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4327)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    run_server(
        Path(args.project),
        config_path=Path(args.config) if args.config else None,
        host=args.host,
        port=args.port,
        open_browser=args.open,
    )


if __name__ == "__main__":
    main()
