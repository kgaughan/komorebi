import os

from flask import Flask, render_template

from . import blog, sri


def create_app():
    app = Flask(__name__)
    app.config.from_envvar("KOMOREBI_SETTINGS")
    app.register_blueprint(blog.blog)
    app.cli.add_command(sri.generate_hashes)

    @app.errorhandler(404)
    def page_not_found(_e):
        return (render_template("404.html"), 404)

    sris = sri.load_sris()

    @app.template_global("sri")
    def get_sri(filename):
        if app.debug:
            return ""
        return sris.get(filename, "")

    return app


def create_wsgi_app():
    return create_app().wsgi_app
