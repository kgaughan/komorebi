import datetime
import typing as t

from flask import url_for

from . import db
from .adjunct import xmlutils


def generate_sitemap(entries: t.Iterable[db.SitemapEntry]) -> str:
    xml = xmlutils.XMLBuilder()
    with xml.within("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"):
        with xml.within("url"):
            xml.loc(url_for("blog.latest", _external=True))
            xml.changefreq("daily")
            xml.priority("0.8")
        for entry in entries:
            with xml.within("url"):
                dt = entry["time_m"].astimezone(datetime.UTC)
                xml.loc(url_for("blog.entry", entry_id=entry["id"], _external=True))
                xml.lastmod(dt.isoformat())
                xml.changefreq("weekly")
                xml.priority("0.5")
    return xml.as_string()
