from flask import Flask, render_template

from . import blog, db, extensions, sri


def create_app(*, testing: bool = False) -> Flask:
    app = Flask(__name__)
    if not testing:
        app.config.from_envvar("KOMOREBI_SETTINGS")
    else:
        app.config.update(
            {
                "TESTING": True,
                "SERVER_NAME": "example.com",
                "APPLICATION_ROOT": "/site/",
                "PREFERRED_URI_SCHEME": "http",
                "CACHE_TYPE": "NullCache",
            }
        )
    app.config["COMPRESS_REGISTER"] = False  # only compress annotated views
    app.config["COMPRESS_MIMETYPES"] = [
        "application/json",
        "text/css",
        "text/html",
        "text/javascript",
        # Missing in 1.14
        "application/xml",
        "application/atom+xml",
    ]
    app.register_blueprint(blog.blog)
    app.cli.add_command(sri.generate_hashes)
    db.init_app(app)
    extensions.cache.init_app(app)
    extensions.compress.init_app(app)

    @app.errorhandler(404)
    def page_not_found(_):
        return (render_template("404.html"), 404)

    sris = sri.load_sris()

    @app.template_global("sri")
    def get_sri(filename: str) -> str:
        if app.debug:
            return ""
        return sris.get(filename, "")

    return app


def create_wsgi_app():
    return create_app().wsgi_app
