"""An [oEmbed](https://oembed.com/) client library.

As a general rule, you'll only ever need the [adjunct.oembed.fetch][] function.
"""

import json
import typing as t
from urllib import error, parse, request
import xml.sax
import xml.sax.handler

from .compat import parse_header

__all__ = ["fetch", "get_oembed"]


class _OEmbedContentHandler(xml.sax.handler.ContentHandler):
    """Pulls the fields out of an XML oEmbed document."""

    _valid_fields: t.ClassVar[list[str]] = [
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
        self.current_field: str | None = None
        self.current_value: list[str] = []
        self.depth = 0
        self.fields: dict[str, str | int] = {}

    def startElement(self, name, attrs) -> None:  # noqa: N802, ARG002
        self.depth += 1
        if self.depth == 2:
            self.current_field = name
            self.current_value = []

    def endElement(self, name) -> None:  # noqa: N802, ARG002
        if self.depth == 2 and self.current_field in self._valid_fields:
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


def fetch(
    url: str,
    max_width: int | None = None,
    max_height: int | None = None,
) -> dict[str, str | int] | None:
    """Fetch the oEmbed document for a resource at `url` from the provider.

    Args:
        url: URL of oEmbed document
        max_width: desired maximum width of the thumbnail, if any
        max_height: desired maximum height of the thumbnail, if any

    Returns:
        An oEmbed document as a dictionary; `None` if the document could not
        be fetched or the content type of the response was not valid for an
        oEmbed document.
    """
    headers = {
        "Accept": ", ".join(_ACCEPTABLE_TYPES.keys()),
        "User-Agent": "adjunct-oembed/1.0",
    }
    try:
        req = request.Request(_build_url(url, max_width, max_height), headers=headers)
        with request.urlopen(req, timeout=5) as fh:
            content_type, _ = parse_header(
                fh.headers.get("content-type", "application/octet-stream"),
            )
            if content_type in _ACCEPTABLE_TYPES:
                parser = _ACCEPTABLE_TYPES[content_type]
                return parser(fh)  # type: ignore
    except error.HTTPError as exc:
        if 400 <= exc.code < 500:
            return None
        raise
    return None


def _parse_xml_oembed_response(fh: t.TextIO) -> dict[str, str | int]:
    """Parse the fields from an XML OEmbed document."""
    handler = _OEmbedContentHandler()
    xml.sax.parse(fh, handler)
    return handler.fields


# Types we'll accept and their parsers. I think it's a design flaw of oEmbed
# that (a) these content types aren't the same as the link types and (b) that
# text/xml (which is deprecated, IIRC) is being used rather than
# application/xml. Just to be perverse, let's support all of that.
_ACCEPTABLE_TYPES = {
    "application/json": json.load,
    "application/json+oembed": json.load,
    "application/xml": _parse_xml_oembed_response,
    "application/xml+oembed": _parse_xml_oembed_response,
    "text/xml": _parse_xml_oembed_response,
    "text/xml+oembed": _parse_xml_oembed_response,
}

_LINK_TYPES = [key for key in _ACCEPTABLE_TYPES if key.endswith("+oembed")]


def _find_first_oembed_link(links: t.Collection[dict[str, str]]) -> str | None:
    """Search for the first valid oEmbed link.

    Args:
        links: a collection of link tags represented as attribute dictionaries

    Returns:
        The value of the `href` attribute of the first one with a valid oEmbed
        MIME type specified in its `type` attribute.
    """
    for link in links:
        if link.get("rel") == "alternate" and link.get("type") in _LINK_TYPES:
            url = link.get("href")
            if url is not None:
                return url
    return None


def get_oembed(
    links: t.Collection[dict[str, str]],
    max_width: int | None = None,
    max_height: int | None = None,
) -> dict[str, str | int] | None:
    """Given a URL, fetch its associated oEmbed information.

    Args:
        links: a collection of link tags represented as attribute dictionaries
        max_width: desired maximum width of the thumbnail, if any
        max_height: desired maximum height of the thumbnail, if any

    Returns:
        An oEmbed document as a dictionary; `None` if the document could not
        be fetched or the content type of the response was not valid for an
        oEmbed document.
    """
    if oembed_url := _find_first_oembed_link(links):
        return fetch(oembed_url, max_width, max_height)
    return None
