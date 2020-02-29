from urllib import parse

from flask import (
    Flask,
    redirect,
    request,
    Response,
    abort,
    render_template,
    url_for,
)
from flask_httpauth import HTTPBasicAuth
import markdown
from passlib.apache import HtpasswdFile

from komorebi import db, forms, utils, xmlutils


FEED_ID = "tag:talideon.com,2001:weblog"


app = Flask(__name__)
app.config.from_envvar("KOMOREBI_SETTINGS")
app.teardown_appcontext(db.close_connection)

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    htpasswd_path = app.config.get("HTPASSWD_PATH")
    if htpasswd_path is not None:
        return HtpasswdFile(htpasswd_path).check_password(username, password)
    return False


@app.route("/")
def latest():
    return render_template("latest.html", entries=db.query_latest())


@app.route("/archive")
def archive():
    return render_template("archive.html", entries=process_archive(db.query_archive()))


def process_archive(records):
    year = None
    last_month = 0
    for record in records:
        # Pad out to the end of the year.
        if record["year"] != year:
            if last_month != 0:
                for i in range(1, 13 - last_month):
                    yield {"n": 0, "year": year, "month": last_month + i}
            year = record["year"]
            last_month = 0

        # Pad out between months in a year.
        if record["month"] - 1 != last_month:
            for i in range(1, record["month"] - last_month):
                yield {"n": 0, "year": record["year"], "month": last_month + i}

        yield record
        last_month = record["month"]


@app.route("/feed")
def feed():
    modified = db.query_last_modified()
    # TODO: ETag

    xml = xmlutils.XMLBuilder()
    with xml.within("feed", xmlns="http://www.w3.org/2005/Atom"):
        xml.title("Inklings")
        xml.subtitle("A stream of random things")
        if modified:
            xml.modified(modified.isoformat())
        with xml.within("author"):
            xml.name("Keith Gaughan")
        xml.id(FEED_ID)
        xml.rights("Copyright (c) Keith Gaughan 2001-2020")
        xml.link(
            rel="alternate",
            type="text/html",
            hreflang="en",
            href=url_for("latest", _external=True),
        )
        xml.link(
            rel="self",
            type="text/html",
            hreflang="en",
            href=url_for("feed", _external=True),
        )

        for entry in db.query_latest():
            with xml.within("entry"):
                xml.title(entry["title"])
                xml.published(utils.to_iso_date(entry["time_c"]))
                xml.updated(utils.to_iso_date(entry["time_m"]))
                xml.id("{}:{}".format(FEED_ID, entry["id"]))
                permalink = url_for("entry", entry_id=entry["id"], _external=True)
                alternate = entry["link"] if entry["link"] else permalink
                xml.link(rel="alternate", type="text/html", href=alternate)
                if entry["link"]:
                    xml.link(rel="related", type="text/html", href=permalink)
                if entry["via"]:
                    xml.link(rel="via", type="text/html", href=entry["via"])
                if entry["note"]:
                    attrs = {"type": "html", "xml:lang": "en", "xml:base": permalink}
                    xml.content(md(entry["note"]), **attrs)

    return Response(xml.as_string(), content_type="application/atom+xml; charset=UTF-8")


@app.route("/<string(length=4):year>-<string(length=2):month>")
def month(year, month):
    entries = db.query_month(int(year), int(month))
    if not entries:
        abort(404)
    return render_template("month.html", entries=entries, dt=dt)


@app.route("/<int:entry_id>")
def entry(entry_id):
    entry = db.query_entry(entry_id)
    if entry is None:
        abort(404)
    return render_template("entry.html", entry=entry)


@app.route("/add", methods=["GET", "POST"])
@auth.login_required
def add_entry():
    form = forms.EntryForm()
    if form.validate_on_submit():
        entry_id = db.add_entry(
            link=form.link.data,
            title=form.title.data,
            via=form.via.data,
            note=form.note.data,
        )
        return redirect(url_for("entry", entry_id=entry_id))
    return render_template("entry_edit.html", form=form)


@app.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@auth.login_required
def edit_entry(entry_id):
    entry = db.query_entry(entry_id)
    if entry is None:
        abort(404)
    form = forms.EntryForm(data=entry)
    if form.validate_on_submit():
        db.update_entry(
            entry_id,
            link=form.link.data,
            title=form.title.data,
            via=form.via.data,
            note=form.note.data,
        )
        return redirect(url_for("entry", entry_id=entry_id))
    return render_template("entry_edit.html", form=form)


@app.errorhandler(404)
def page_not_found(e):
    return (render_template("404.html"), 404)


@app.template_filter("markdown")
def md(text):
    return markdown.markdown(
        text,
        output_format="html",
        extensions=[
            "smarty",
            "tables",
            "attr_list",
            "def_list",
            "fenced_code",
            "admonition",
        ],
    )


@app.template_filter()
def extract_hostname(url):
    return parse.urlparse(url).netloc
