import os

from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from komorebi import blog, sri


def adjust_app_prefix(app, prefix="/"):
    """
    Flask's 'APPLICATION_ROOT' setting is misleading. You'd think it'd be a
    way to set the root of the application (I know!) in the URL, but it
    doesn't. Instead, you need a hack like this.

    There are two ways to set the prefix: you can hardwire it into the code or
    set the prefix using the environment variable `APP_PREFIX`. If the default
    of `/` is used, the wrapper isn't applied. Any trailing slash is normalised.
    """
    prefix = os.environ.get("APP_PREFIX", prefix).rstrip("/") + "/"
    if prefix == "/":
        return app

    def wrapper(environ, start_response):
        environ["SCRIPT_NAME"] = prefix
        path_info = environ["PATH_INFO"]
        if path_info.startswith(prefix):
            environ["PATH_INFO"] = path_info[len(prefix) :]
        return app(environ, start_response)

    return wrapper


def create_app():
    app = Flask(__name__)
    app.config.from_envvar("KOMOREBI_SETTINGS")
    app.register_blueprint(blog.blog)
    app.cli.add_command(sri.generate_hashes)

    @app.errorhandler(404)
    def page_not_found(_e):
        return (render_template("404.html"), 404)

    return app


def create_wsgi_app():
    return ProxyFix(adjust_app_prefix(create_app().wsgi_app))
