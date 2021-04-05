import argparse
import logging
from wsgiref.simple_server import make_server, WSGIRequestHandler

from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from komorebi import blog


class RequestHandler(WSGIRequestHandler):

    script_name = "/"

    def get_environ(self):
        environ = super().get_environ()
        if self.script_name != "/":
            environ["SCRIPT_NAME"] = self.script_name
            path_info = environ["PATH_INFO"]
            if path_info.startswith(self.script_name):
                environ["PATH_INFO"] = path_info[len(self.script_name) :]
        return environ


def make_parser():
    parser = argparse.ArgumentParser(description="Run with wsgiref")
    parser.add_argument(
        "--host",
        help="Host to run on",
        default="",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to run on",
        default=8000,
    )
    parser.add_argument(
        "--script-name",
        help="Value to use for SCRIPT_NAME",
        default="/",
    )
    parser.add_argument(
        "--dev",
        help="Run using the Flask development server",
        action="store_true",
    )
    return parser


app = Flask(__name__)
app.config.from_envvar("KOMOREBI_SETTINGS")
app.register_blueprint(blog.blog)


@app.errorhandler(404)
def page_not_found(_e):
    return (render_template("404.html"), 404)


args = make_parser().parse_args()
if args.dev:
    app.run(host=args.host, port=args.port, debug=True)
else:
    logging.basicConfig(level=logging.WARNING)
    with make_server(
        args.host,
        args.port,
        ProxyFix(app.wsgi_app),
        handler_class=type(
            "RH",
            (RequestHandler,),
            dict(script_name=args.script_name),
        ),
    ) as server:
        server.serve_forever()
