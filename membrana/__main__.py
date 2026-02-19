"""Entry point: python -m membrana"""

import argparse
import os
import threading
import webbrowser

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Membrana — membrane diagram generator")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    args = parser.parse_args()

    # Auto-detect container/cloud environments
    is_container = os.environ.get("DOCKER", "") or os.environ.get("SPACE_ID", "")

    if not args.no_browser and not is_container:
        def open_browser():
            webbrowser.open(f"http://{args.host}:{args.port}")
        threading.Timer(1.5, open_browser).start()

    uvicorn.run(
        "membrana.server.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=not is_container,
    )


if __name__ == "__main__":
    main()
