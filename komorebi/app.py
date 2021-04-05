from flask import (
    Flask,
    render_template,
)

from . import blog


app = Flask(__name__)
app.config.from_envvar("KOMOREBI_SETTINGS")
app.register_blueprint(blog.blog)


@app.errorhandler(404)
def page_not_found(e):
    return (render_template("404.html"), 404)
