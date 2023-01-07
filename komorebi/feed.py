from datetime import datetime
from typing import Iterable, Optional, TypedDict

from flask import url_for

from . import formatting, time, xmlutils

Entry = TypedDict(
    "Entry",
    {
        "id": str,
        "title": str,
        "time_c": str,
        "time_m": str,
        "link": Optional[str],
        "via": Optional[str],
        "html": Optional[str],
        "note": Optional[str],
    },
)


def generate_feed(
    title: str,
    author: str,
    feed_id: str,
    entries: Iterable[Entry],
    subtitle: Optional[str] = None,
    rights: Optional[str] = None,
    modified: Optional[datetime] = None,
):
    xml = xmlutils.XMLBuilder()
    with xml.within("feed", xmlns="http://www.w3.org/2005/Atom"):
        xml.title(title)
        if subtitle:
            xml.subtitle(subtitle)
        if modified:
            xml.updated(modified.isoformat())
        with xml.within("author"):
            xml.name(author)
        xml.id(feed_id)
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

        for entry in entries:
            add_entry(xml, feed_id, entry)
    return xml.as_string()


def add_entry(xml: xmlutils.XMLBuilder, feed_id: str, entry: Entry):
    with xml.within("entry"):
        xml.title(entry["title"])
        xml.published(time.to_iso_date(entry["time_c"]))
        xml.updated(time.to_iso_date(entry["time_m"]))
        xml.id(f"{feed_id}:{entry['id']}")
        permalink = url_for(".entry", entry_id=entry["id"], _external=True)
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
