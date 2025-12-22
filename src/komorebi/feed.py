import datetime
import typing as t

from flask import url_for

from . import db, formatting
from .adjunct import xmlutils


def generate_feed(
    title: str,
    author: str,
    feed_id: str,
    entries: t.Iterable[db.Entry],
    subtitle: str | None = None,
    rights: str | None = None,
    modified: datetime.datetime | None = None,
) -> str:
    xml = xmlutils.XMLBuilder()
    with xml.within("feed", xmlns="http://www.w3.org/2005/Atom"):
        xml.title(title)
        if subtitle:
            xml.subtitle(subtitle)
        if modified:
            xml.updated(modified.replace(tzinfo=datetime.UTC).isoformat())
        with xml.within("author"):
            xml.name(author)
        xml.id(feed_id)
        if rights:
            xml.rights(rights)
        xml.link(
            rel="alternate",
            type="text/html",
            hreflang="en",
            href=url_for("blog.latest", _external=True),
        )
        xml.link(
            rel="self",
            type="application/atom+xml",
            hreflang="en",
            href=url_for("blog.feed", _external=True),
        )

        for entry in entries:
            add_entry(xml, feed_id, entry)
    return xml.as_string()


def add_entry(xml: xmlutils.XMLBuilder, feed_id: str, entry: db.Entry) -> None:
    with xml.within("entry"):
        xml.title(entry["title"])
        xml.published(entry["time_c"].replace(tzinfo=datetime.UTC).isoformat())
        xml.updated(entry["time_m"].replace(tzinfo=datetime.UTC).isoformat())
        xml.id(f"{feed_id}:{entry['id']}")
        permalink = url_for("blog.entry", entry_id=entry["id"], _external=True)
        alternate = entry["link"] or permalink
        xml.link(rel="alternate", type="text/html", href=alternate)
        if entry["link"]:
            xml.link(rel="related", type="text/html", href=permalink)
        if entry["via"]:
            xml.link(rel="via", type="text/html", href=entry["via"])
        if entry["note"] or entry["html"]:
            content = f"<div>{entry['html']}</div>" if entry["html"] else ""
            content += formatting.render_markdown(entry["note"])
            attrs = {
                "type": "html",
                "xml:lang": "en",
                "xml:base": permalink,
            }
            xml.content(content, **attrs)
