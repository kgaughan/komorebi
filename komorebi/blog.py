from sqlite3 import IntegrityError
from urllib import parse

from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from flask_httpauth import HTTPBasicAuth
import markdown
from passlib.apache import HtpasswdFile

from . import db, embeds, forms, time, xmlutils

blog = Blueprint("blog", __name__)
blog.add_app_template_filter(time.to_iso_date)
blog.after_request(db.close_connection)

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    htpasswd_path = current_app.config.get("HTPASSWD_PATH")
    if htpasswd_path is not None:
        return HtpasswdFile(htpasswd_path).check_password(username, password)
    return False


@blog.route("/")
def latest():
    return render_template("latest.html", entries=db.query_latest())


@blog.route("/archive")
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
                    yield {
                        "n": 0,
                        "year": year,
                        "month": last_month + i,
                    }
            year = record["year"]
            last_month = 0

        # Pad out between months in a year.
        if record["month"] - 1 != last_month:
            for i in range(1, record["month"] - last_month):
                yield {
                    "n": 0,
                    "year": record["year"],
                    "month": last_month + i,
                }

        yield record
        last_month = record["month"]


@blog.route("/feed")
def feed():
    response = Response(content_type="application/atom+xml; charset=UTF-8")
    response.cache_control.public = True
    response.cache_control.max_age = 3600
    modified = db.query_last_modified()
    response.last_modified = modified
    if request.if_modified_since and modified <= request.if_modified_since:
        return response.make_conditional(request)

    feed_id = current_app.config["FEED_ID"]

    xml = xmlutils.XMLBuilder()
    with xml.within("feed", xmlns="http://www.w3.org/2005/Atom"):
        xml.title(current_app.config.get("BLOG_TITLE", "My Weblog"))
        subtitle = current_app.config.get("BLOG_SUBTITLE")
        if subtitle:
            xml.subtitle(subtitle)
        if modified:
            xml.updated(modified.isoformat())
        with xml.within("author"):
            xml.name(current_app.config["BLOG_AUTHOR"])
        xml.id(feed_id)
        rights = current_app.config.get("BLOG_RIGHTS")
        if rights:
            xml.rights(rights)
        xml.link(
            rel="alternate",
            type="text/html",
            hreflang="en",
            href=url_for(".latest", _external=True),
        )
        xml.link(
            rel="self",
            type="text/html",
            hreflang="en",
            href=url_for(".feed", _external=True),
        )

        for entry in db.query_latest():
            with xml.within("entry"):
                xml.title(entry["title"])
                xml.published(time.to_iso_date(entry["time_c"]))
                xml.updated(time.to_iso_date(entry["time_m"]))
                xml.id(f"{feed_id}:{entry['id']}")
                permalink = url_for(".entry", entry_id=entry["id"], _external=True)
                alternate = entry["link"] if entry["link"] else permalink
                xml.link(rel="alternate", type="text/html", href=alternate)
                if entry["link"]:
                    xml.link(rel="related", type="text/html", href=permalink)
                if entry["via"]:
                    xml.link(rel="via", type="text/html", href=entry["via"])
                if entry["note"] or entry["html"]:
                    content = ""
                    if entry["html"]:
                        content += f"<div>{entry['html']}</div>"
                    if entry["note"]:
                        content += md(entry["note"])
                    attrs = {"type": "html", "xml:lang": "en", "xml:base": permalink}
                    xml.content(content, **attrs)
    response.set_data(xml.as_string())

    return response


@blog.route("/<string(length=4):year>-<string(length=2):month>", endpoint="month")
def render_month(year, month):
    entries = db.query_month(int(year), int(month))
    if not entries:
        abort(404)
    dt = f"{year}-{month}"
    return render_template("month.html", entries=entries, dt=dt)


@blog.route("/<int:entry_id>", endpoint="entry")
def render_entry(entry_id):
    entry = db.query_entry(entry_id)
    if entry is None:
        abort(404)
    return render_template("entry.html", entry=entry)


@blog.route("/add", methods=["GET", "POST"])
@auth.login_required
def add_entry():
    form = forms.EntryForm()
    if form.validate_on_submit():
        # Fetch the embed _first_ to prevent a database lockup
        markup = embeds.fetch_embed(form.link.data)

        try:
            entry_id = db.add_entry(
                link=form.link.data,
                title=form.title.data,
                via=form.via.data,
                note=form.note.data,
            )
        except IntegrityError:
            flash("That links already exists", "error")
        else:
            if markup:
                db.add_oembed(entry_id, markup)

            return redirect(url_for(".entry", entry_id=entry_id))
    return render_template("entry_edit.html", form=form)


@blog.route("/<int:entry_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for(".entry", entry_id=entry_id))
    return render_template("entry_edit.html", form=form)


@blog.app_template_filter("markdown")
def md(text):
    if text is None:
        return ""
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


@blog.app_template_filter()
def extract_hostname(url):
    return parse.urlparse(url).netloc
