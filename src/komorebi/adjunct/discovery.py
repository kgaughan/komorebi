"""Discovery via HTML <link> elements.

For most purposes, [adjunct.discovery.fetch_meta][] should do anything you
need.
"""

import contextlib
from html.parser import HTMLParser
import io
import logging
import typing as t
from urllib import parse, request

from .compat import parse_header

__all__ = ["Extractor", "fetch_meta", "fix_attributes"]

logger = logging.getLogger(__name__)


# pylint: disable-msg=R0904
class Extractor(HTMLParser):
    """
    A simple subclass of [html.parser.HTMLParser][] for extracting metadata
    like from `<meta>` and `<link>` tags from the header of a HTML document.

    It's recommended you use the [adjunct.discovery.Extractor.extract][] class
    method rather than instantiating this class directly.

    Args:
        base: the base URL for the document

    Attributes:
        base: the base URL for the document; the `<base>` tag is used if found
        collected: any collected links; each entry is a dictionary of the attributes
        properties: any collected `<meta>` tags with `property` and `content` attributes
    """

    def __init__(self, base: str) -> None:
        super().__init__()
        self.base: str = base
        self.collected: list[dict[str, str]] = []
        self.properties: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        fixed_attrs = fix_attributes(attrs)
        if tag == "link":
            self._append(fixed_attrs)
        elif tag == "base" and "href" in fixed_attrs:
            self.base = parse.urljoin(self.base, fixed_attrs["href"])
        elif tag == "meta" and "property" in fixed_attrs and "content" in fixed_attrs:
            self.properties.append((fixed_attrs["property"], fixed_attrs["content"]))

    def _append(self, attrs: dict[str, str]) -> None:
        """Append the given set of attributes onto our list.

        By separating this out, we can modify the behaviour in subclasses.
        """
        self.collected.append(attrs)

    def _fix_href(self, href: str) -> str:
        """Make the given href absolute to any previously discovered <base> tag."""
        return parse.urljoin(self.base, href)

    @classmethod
    def extract(cls, fh: io.IOBase, base: str = ".", encoding: str = "UTF-8") -> "Extractor":
        """Extract the link tags from header of a HTML document to be read.

        Args:
            fh: a file-like object to read the HTML document from.
            base: A base path/URL to use of URLs in the document. Note that the `<base>` tag will take priority.
            encoding: default text encoding to assume for the document.

        Returns:
            The parser with all links extracted and canonicalised.
        """
        parser = cls(base)
        with contextlib.closing(parser):
            for chunk in _safe_slurp(fh, encoding=encoding):
                parser.feed(chunk)

        # Canonicalise the URL paths.
        for link in parser.collected:
            if "href" in link:
                link["href"] = parser._fix_href(link["href"])

        return parser

    def error(self, message: str) -> None:
        # This method is undocumented in HTMLParser, but pylint is moaning
        # about it, so...
        logger.error("Error in Extractor: %s", message)  # pragma: no cover


def _safe_slurp(fh: io.IOBase, chunk_size: int = 65536, encoding: str = "UTF-8") -> t.Iterator[str]:
    """Safely convert file object, converting it to the given file encoding.

    This handles situations such as UTF-8 characters on chunk boundaries
    gracefully.

    Args:
        fh: a file-like object to read the data from.
        chunk_size: what should the approximate maximum size of each chunk be
        encoding: text encoding to assume for the input data.

    Yields:
        Chunks of string data read from the file-like object.
    """
    # Enforce a lower end: 6 will give us 31 bits of codepoint space coverage,
    # though RFC3629 mandates a max of 4 for compatibility with UTF-16. The
    # extra leeway shouldn't be a bad thing though. I'm hoping this is fine for
    # other long encodings too.
    chunk_size = max(chunk_size, 6)
    prelude = None
    while True:
        chunk = fh.read(chunk_size)
        if not chunk:
            break
        if prelude is not None:
            chunk = prelude + chunk
            prelude = None
        try:
            decoded = chunk.decode(encoding)
        except UnicodeDecodeError as exc:
            # If the error is at the start, there's a genuine issue.
            if exc.start == 0:
                raise
            decoded = chunk[: exc.start].decode()
            prelude = chunk[exc.start :]
        yield decoded


def fix_attributes(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    """Normalise and clean up the attributes, and put them in a dict.

    Attribute names are normalised to lowercase; whitespace within values is
    trimmed; if the value of an attribute is `None`, it's replaced with an
    empty string; and the values of the `rel` and `type` attributes are
    converted to lowercase.

    Args:
        attrs: raw attributes

    Returns:
        cleaned-up attributes
    """
    result = {}
    for attr, value in attrs:
        attr = attr.lower()
        if value is None:
            result[attr] = ""  # The attribute is present, but has no value
            continue
        if attr in ("rel", "type"):
            value = value.lower()
        result[attr] = value.strip()
    return result


def fetch_meta(
    url: str,
    extractor: type[Extractor] = Extractor,
) -> tuple[t.Collection[dict[str, str]], t.Collection[tuple[str, str]]]:
    """Extract the <link> tags from the HTML document at the given URL.

    As this is fetching the document over HTTP, it can also support the
    [Link header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Link).

    Args:
        url: URL of the document to extract the link tags from.
        extractor: an Extractor subclass

    Returns:
        The link tag data and any properties discovered in meta tags.
    """
    links = []
    properties = []

    req = request.Request(url, headers={"User-Agent": "adjunct-discovery/1.0"})
    with request.urlopen(req, timeout=5) as fh:
        info = fh.info()
        for name, value in info.items():
            if name.lower() == "link":
                href, attrs = parse_header(value)
                if not href.startswith("<") or not href.endswith(">"):
                    continue
                href = href[1:-1]
                attrs["href"] = parse.urljoin(url, href)
                links.append(attrs)

        content_type = info.get("Content-Type", "application/octet-stream")
        content_type, attrs = parse_header(content_type)
        if content_type in ("text/html", "application/xhtml+xml"):
            encoding = attrs.get("charset", "UTF-8")
            extracted = extractor.extract(fh, url, encoding=encoding)
            links += extracted.collected
            properties = extracted.properties

    return links, properties
