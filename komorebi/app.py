from urllib import parse

from flask import (
    Flask,
    render_template,
)

from . import blog, db, time


app = Flask(__name__)
app.config.from_envvar("KOMOREBI_SETTINGS")
app.teardown_appcontext(db.close_connection)
app.add_template_filter(time.to_iso_date)
app.register_blueprint(blog.blog)


@app.errorhandler(404)
def page_not_found(e):
    return (render_template("404.html"), 404)


@app.template_filter()
def extract_hostname(url):
    return parse.urlparse(url).netloc
