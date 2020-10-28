"""
Discovery via HTML <link> elements.
"""

import cgi
import contextlib
from html.parser import HTMLParser
from urllib import parse, request


__all__ = ["Extractor", "fetch_links", "fix_attributes"]


# pylint: disable-msg=R0904
class Extractor(HTMLParser):
    """
    A simple subclass of `HTMLParser` for extracting metadata like from <meta>
    and <link> tags from the header of a HTML document.
    """

    def __init__(self, base):
        super().__init__()
        self.active = False
        self.finished = False
        self.base = base
        self.collected = []
        self.properties = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "head":
            self.active = True
        elif self.active:
            attrs = fix_attributes(attrs)
            if tag == "link":
                self.append(attrs)
            elif tag == "base" and "href" in attrs:
                self.base = parse.urljoin(self.base, attrs["href"])
            elif tag == "meta" and "property" in attrs and "content" in attrs:
                self.properties.append((attrs["property"], attrs["content"]))

    def handle_endtag(self, tag):
        if tag.lower() == "head":
            self.active = False
            self.finished = True

    def append(self, attrs):
        """
        Append the given set of attributes onto our list.

        By separating this out, we can modify the behaviour in subclasses.
        """
        self.collected.append(attrs)

    def fix_href(self, href):
        """
        Make the given href absolute to any previously discovered <base> tag.
        """
        return parse.urljoin(self.base, href)

    @classmethod
    def extract(cls, fh, base=".", encoding="UTF-8"):
        """
        Extract the link tags from header of a HTML document to be read from
        the file object, `fh`. The return value is a list of dicts where the
        values of each are the attributes of the link elements encountered.
        """
        parser = cls(base)
        with contextlib.closing(parser):
            for chunk in safe_slurp(fh, encoding=encoding):
                parser.feed(chunk)
                if parser.finished:
                    break

        # Canonicalise the URL paths.
        for link in parser.collected:
            if "href" in link:
                link["href"] = parser.fix_href(link["href"])

        return parser


def safe_slurp(fh, chunk_size=65536, encoding="UTF-8"):
    """
    Safely convert file object, converting it to the given file encoding.

    This handles situations such as UTF-8 characters on chunk boundaries
    gracefully.
    """
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


def fix_attributes(attrs):
    """
    Normalise and clean up the attributes, and put them in a dict.
    """
    result = {}
    for attr, value in attrs:
        attr = attr.lower()
        if value is None:
            result[attr] = True  # The attribute is present, but has no value
            continue
        if attr in ("rel", "type"):
            value = value.lower()
        result[attr] = value.strip()
    return result


def fetch_links(url, extractor=Extractor):
    """
    Extract the <link> tags from the HTML document at the given URL.
    """
    links = []

    req = request.Request(url, headers={"User-Agent": "adjunct-discovery/1.0"})
    with request.urlopen(req) as fh:
        info = fh.info()
        for name, value in info.items():
            if name.lower() == "link":
                href, attrs = cgi.parse_header(value)
                attrs["href"] = parse.urljoin(url, href)
                links.append(attrs)

        content_type = info.get("Content-Type", "application/octet-stream")
        content_type, attrs = cgi.parse_header(content_type)
        if content_type in ("text/html", "application/xhtml+xml"):
            encoding = attrs.get("charset", "UTF-8")
            links += extractor.extract(fh, url, encoding=encoding).collected

    return links
