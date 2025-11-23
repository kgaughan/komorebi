from sqlite3 import IntegrityError
import typing as t
from urllib import parse

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_httpauth import HTTPBasicAuth

from . import db, embeds, formatting, forms
from .adjunct import passkit, time
from .feed import generate_feed

blog = Blueprint("blog", __name__)
blog.add_app_template_filter(time.to_iso_date)
blog.add_app_template_filter(time.to_wayback_date)
blog.add_app_template_filter(formatting.render_markdown, "markdown")
blog.after_request(db.close_connection)

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username: str, password: str):
    passwd_path = current_app.config.get("PASSWD_PATH")
    if passwd_path is not None:
        return passkit.JSONPasswdFile(passwd_path).check_password(username, password)
    return False


@blog.route("/")
def latest() -> str:
    return render_template("latest.html", entries=db.query_latest())


@blog.route("/archive")
def archive() -> str:
    return render_template("archive.html", entries=process_archive(db.query_archive()))


def process_archive(records: t.Iterable[db.ArchiveMonth]) -> t.Iterable[db.ArchiveMonth]:
    year = None
    last_month = 0
    for record in records:
        # Pad out to the end of the year.
        if record["year"] != year:
            if last_month != 0:
                for i in range(1, 13 - last_month):
                    yield {
                        "n": 0,
                        "year": year or 0,
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
def feed() -> Response:
    response = Response(content_type="application/atom+xml; charset=UTF-8")
    response.cache_control.public = True
    response.cache_control.max_age = 3600
    modified = db.query_last_modified()
    response.last_modified = modified

    if request.if_modified_since and modified is not None and modified <= request.if_modified_since:
        return response.make_conditional(request)  # type: ignore

    response.set_data(
        generate_feed(
            feed_id=current_app.config["FEED_ID"],
            title=current_app.config.get("BLOG_TITLE", "My Weblog"),
            subtitle=current_app.config.get("BLOG_SUBTITLE"),
            author=current_app.config["BLOG_AUTHOR"],
            rights=current_app.config.get("BLOG_RIGHTS"),
            modified=modified,
            entries=db.query_latest(),
        )
    )

    return response


@blog.route("/<string(length=4):year>-<string(length=2):month>", endpoint="month")
def render_month(year: str, month: str) -> str:
    entries = db.query_month(int(year), int(month))
    if not entries:
        abort(404)
    dt = f"{year}-{month}"
    return render_template("month.html", entries=entries, dt=dt)


@blog.route("/<int:entry_id>", endpoint="entry")
def render_entry(entry_id: int) -> str:
    entry = db.query_entry(entry_id)
    if entry is None:
        abort(404)
    return render_template("entry.html", entry=entry)


@blog.route("/add", methods=["GET", "POST"])
@auth.login_required
def add_entry() -> Response | str:
    form = forms.EntryForm()
    if form.is_submitted() and form.validate():
        # Fetch the embed _first_ to prevent a database lockup
        markup = embeds.fetch_embed(form.link.data)

        try:
            entry_id = db.add_entry(
                link=form.link.data,
                title=form.title.data,  # type: ignore
                via=form.via.data,
                note=form.note.data,
            )
        except IntegrityError:
            flash("That links already exists", "error")
        else:
            if markup:
                db.add_oembed(entry_id, markup)

            return redirect(url_for(".entry", entry_id=entry_id))  # type: ignore
    return render_template("entry_edit.html", form=form)


@blog.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@auth.login_required
def edit_entry(entry_id: int) -> str:
    entry = db.query_entry(entry_id)
    if entry is None:
        abort(404)
    form = forms.EntryForm(data=entry)
    if form.validate_on_submit():
        db.update_entry(
            entry_id,
            link=form.link.data,
            title=form.title.data,  # type: ignore
            via=form.via.data,
            note=form.note.data,
        )
        return redirect(url_for(".entry", entry_id=entry_id))  # type: ignore
    return render_template("entry_edit.html", form=form)


@blog.app_template_filter()
def extract_hostname(url: str) -> str:
    return parse.urlparse(url).netloc
