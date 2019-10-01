#!/usr/bin/env python3

import argparse
import os
from wsgiref.simple_server import make_server

from komorebi.app import app


def main():
    parser = argparse.ArgumentParser(description="Run with wsgiref")
    parser.add_argument("--host", help="Host to run on", default="")
    parser.add_argument("--port", type=int, help="Port to run on", default=8000)
    args = parser.parse_args()

    with make_server(args.host, args.port, app.wsgi_app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
