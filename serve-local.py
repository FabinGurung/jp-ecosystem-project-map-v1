#!/usr/bin/env python3
"""Serve this static site locally and open it in the default browser."""

from __future__ import annotations

import argparse
import os
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    os.chdir(root)
    address = ("127.0.0.1", args.port)
    url = f"http://{address[0]}:{address[1]}/"
    server = ThreadingHTTPServer(address, SimpleHTTPRequestHandler)

    print(f"Serving JP Ecosystem Operational Project Map at {url}")
    print("Keep this window open. Press Ctrl+C to stop.")
    threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
