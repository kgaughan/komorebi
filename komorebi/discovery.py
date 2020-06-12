"""
Discovery via HTML <link> elements.
"""

import contextlib
from html.parser import HTMLParser
from urllib import parse, request


__all__ = ["LinkExtractor", "fetch_links", "fix_attributes"]


# pylint: disable-msg=R0904
class LinkExtractor(HTMLParser):
    """
    A simple subclass of `HTMLParser` for extracting <link> tags from the
    header of a HTML document.
    """

    def __init__(self, base):
        super().__init__()
        self.active = False
        self.finished = False
        self.base = base
        self.collected = []

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
    def extract(cls, fh, base="."):
        """
        Extract the link tags from header of a HTML document to be read from
        the file object, `fh`. The return value is a list of dicts where the
        values of each are the attributes of the link elements encountered.
        """
        parser = cls(base)
        with contextlib.closing(parser):
            while not parser.finished:
                chunk = fh.read(2048)
                if not chunk:
                    break
                parser.feed(chunk.decode("UTF-8"))

        # Canonicalise the URL paths.
        for link in parser.collected:
            if "href" in link:
                link["href"] = parser.fix_href(link["href"])

        return parser.collected


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


def fetch_links(url, extractor=LinkExtractor):
    """
    Extract the <link> tags from the HTML document at the given URL.
    """
    with request.urlopen(url) as fh:
        return extractor.extract(fh, url)
