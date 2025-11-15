"""
An oEmbed_ client library.

.. _oEmbed: http://oembed.com/
"""

import json
import typing as t
from urllib import error, parse, request
import xml.sax
import xml.sax.handler

from .compat import parse_header

__all__ = ["get_oembed"]


# pylint: disable-msg=C0103
class OEmbedContentHandler(xml.sax.handler.ContentHandler):
    """
    Pulls the fields out of an XML oEmbed document.
    """

    valid_fields: t.ClassVar[list[str]] = [
        "type",
        "version",
        "title",
        "cache_age",
        "author_name",
        "author_url",
        "provider_name",
        "provider_url",
        "thumbnail_url",
        "thumbnail_width",
        "thumbnail_height",
        "width",
        "height",
        "html",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.current_field = None
        self.current_value = []
        self.depth = 0
        self.fields = {}

    def startElement(self, name, attrs) -> None:  # noqa: N802, ARG002
        self.depth += 1
        if self.depth == 2:
            self.current_field = name
            self.current_value = []

    def endElement(self, name) -> None:  # noqa: N802, ARG002
        if self.depth == 2 and self.current_field in self.valid_fields:
            self.fields[self.current_field] = "".join(self.current_value)
        self.depth -= 1

    def characters(self, content) -> None:
        if self.depth == 2:
            self.current_value.append(content)


def _build_url(
    url: str,
    max_width: int | None,
    max_height: int | None,
) -> str:
    if additional := [
        (key, value) for key, value in (("maxwidth", max_width), ("maxheight", max_height)) if value is not None
    ]:
        url += f"&{parse.urlencode(additional)}"
    return url


def fetch_oembed_document(
    url: str,
    max_width: int | None = None,
    max_height: int | None = None,
) -> dict | None:
    """
    Fetch the oEmbed document for a resource at `url` from the provider. If you
    want to constrain the dimensions of the thumbnail, specify the maximum
    width in `max_width` and the maximum height in `max_height`.
    """
    headers = {
        "Accept": ", ".join(ACCEPTABLE_TYPES.keys()),
        "User-Agent": "adjunct-oembed/1.0",
    }
    try:
        req = request.Request(_build_url(url, max_width, max_height), headers=headers)
        with request.urlopen(req, timeout=5) as fh:
            content_type, _ = parse_header(
                fh.headers.get("content-type", "application/octet-stream"),
            )
            if content_type in ACCEPTABLE_TYPES:
                parser = ACCEPTABLE_TYPES[content_type]
                return parser(fh)  # type: ignore
    except error.HTTPError as exc:
        if 400 <= exc.code < 500:
            return None
        raise
    return None


def _parse_xml_oembed_response(fh: t.TextIO) -> dict[str, str | int]:
    """
    Parse the fields from an XML OEmbed document.
    """
    handler = OEmbedContentHandler()
    xml.sax.parse(fh, handler)
    return handler.fields


# Types we'll accept and their parsers. I think it's a design flaw of oEmbed
# that (a) these content types aren't the same as the link types and (b) that
# text/xml (which is deprecated, IIRC) is being used rather than
# application/xml. Just to be perverse, let's support all of that.
ACCEPTABLE_TYPES = {
    "application/json": json.load,
    "application/json+oembed": json.load,
    "application/xml": _parse_xml_oembed_response,
    "application/xml+oembed": _parse_xml_oembed_response,
    "text/xml": _parse_xml_oembed_response,
    "text/xml+oembed": _parse_xml_oembed_response,
}

LINK_TYPES = [key for key in ACCEPTABLE_TYPES if key.endswith("+oembed")]


def find_first_oembed_link(links: t.Collection[dict]) -> str | None:
    """
    Search for the first valid oEmbed link.
    """
    for link in links:
        if link.get("rel") == "alternate" and link.get("type") in LINK_TYPES:
            url = link.get("href")
            if url is not None:
                return url
    return None


def get_oembed(
    links: t.Collection[dict],
    max_width: int | None = None,
    max_height: int | None = None,
) -> dict | None:
    """
    Given a URL, fetch its associated oEmbed information.
    """
    if oembed_url := find_first_oembed_link(links):
        return fetch_oembed_document(oembed_url, max_width, max_height)
    return None
