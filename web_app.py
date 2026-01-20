from __future__ import annotations

import argparse
import http.server
import socketserver
import webbrowser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
INDEX_FILE = TEMPLATES_DIR / "standalone_editor.html"


class EditorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(TEMPLATES_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.path = "/standalone_editor.html"
        super().do_GET()


def run_server(host: str, port: int, open_browser: bool) -> None:
    if not INDEX_FILE.exists():
        raise FileNotFoundError(f"Missing web template: {INDEX_FILE}")

    address = (host, port)
    with socketserver.ThreadingTCPServer(address, EditorHandler) as httpd:
        url = f"http://{host}:{port}/"
        print(f"Web editor running at {url}")
        if open_browser:
            webbrowser.open(url)
        httpd.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the web-based editor.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=5173, help="Bind port")
    parser.add_argument(
        "--no-browser", action="store_true", help="Do not open browser"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_server(args.host, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
