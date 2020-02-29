#!/usr/bin/env python3
#
# A simple application runner using wsgiref.
#

import argparse
from wsgiref.simple_server import make_server, WSGIRequestHandler

from komorebi.app import app


class RequestHandler(WSGIRequestHandler):

    script_name = None

    def get_environ(self):
        environ = super().get_environ()
        if self.script_name and self.script_name != "/":
            environ["SCRIPT_NAME"] = self.script_name
            path_info = environ["PATH_INFO"]
            if path_info.startswith(self.script_name):
                environ["PATH_INFO"] = path_info[len(self.script_name):]
        return environ


def main():
    parser = argparse.ArgumentParser(description="Run with wsgiref")
    parser.add_argument("--host", help="Host to run on", default="")
    parser.add_argument("--port", type=int, help="Port to run on", default=8000)
    parser.add_argument("--script-name", help="Value to use for SCRIPT_NAME", default="/")
    args = parser.parse_args()

    class RH(RequestHandler):
        script_name = args.script_name

    with make_server(args.host, args.port, app.wsgi_app, handler_class=RH) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
