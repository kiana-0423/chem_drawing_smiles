"""Lightweight HTTP server to launch the standalone HTML chemical editor."""

from __future__ import annotations

import argparse
import socket
import socketserver
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
ENTRY_FILE = "standalone_editor.html"


class _ThreadingHTTPServer(ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class _RootHandler(SimpleHTTPRequestHandler):
    """Serve the standalone editor as the root page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(TEMPLATE_DIR), **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = f"/{ENTRY_FILE}"
        return super().do_GET()


def _find_available_port(preferred: int) -> int:
    port = preferred
    while port < preferred + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    raise RuntimeError("Unable to find an available port in the specified range.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port",
        type=int,
        default=5173,
        help="Port to bind the local server (default: 5173).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the editor in a browser window.",
    )
    args = parser.parse_args()

    port = _find_available_port(args.port)

    server = _ThreadingHTTPServer(("127.0.0.1", port), _RootHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}/"
    print(f"Serving standalone editor at {url}")

    if not args.no_browser:
        try:
            webbrowser.open(url, new=2)
        except Exception as error:  # pragma: no cover - best effort only
            print(f"Failed to open browser automatically: {error!r}")

    print("Press Ctrl+C to stop the server.")
    try:
        thread.join()
    except KeyboardInterrupt:
        print("\nShutting down…")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
