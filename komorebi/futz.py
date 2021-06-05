"""
Futz with OEmbed data to fix it up.
"""

import dataclasses
import html
from html.parser import HTMLParser
import io
import logging

logger = logging.getLogger(__name__)

# See: https://html.spec.whatwg.org/multipage/syntax.html#void-elements
SELF_CLOSING = {
    "area",
    "base",
    "br",
    "col",
    "command",
    "embed",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclasses.dataclass
class Element:
    tag: str
    attrs: dict = dataclasses.field(default_factory=dict)
    children: list = dataclasses.field(default_factory=list)

    def __getitem__(self, i):
        return self.children[i]

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def serialize(self, dest=None) -> io.TextIOBase:
        if dest is None:
            dest = io.StringIO()
        if self.tag is not None:
            dest.write("<" + self.tag)
            for key, value in self.attrs.items():
                dest.write(" " + key)
                if value is not None:
                    dest.write('="' + html.escape(value, quote=True) + '"')
            dest.write(">")
        for child in self.children:
            if isinstance(child, str):
                dest.write(html.escape(child, quote=False))
            elif isinstance(child, Element):
                child.serialize(dest)
        if self.tag is not None and self.tag not in SELF_CLOSING:
            dest.write("</" + self.tag + ">")

        return dest


class Parser(HTMLParser):
    """
    Parses a HTML document into
    """

    def __init__(self):
        super().__init__()
        self.root = Element(tag=None)
        self.stack = [self.root]

    @property
    def top(self):
        return self.stack[-1]

    def handle_starttag(self, tag, attrs):
        elem = Element(tag=tag, attrs=dict(attrs))
        self.top.children.append(elem)
        if tag not in SELF_CLOSING:
            self.stack.append(elem)

    def handle_startendtag(self, tag, attrs):
        elem = Element(tag=tag, attrs=attrs)
        self.top.children.append(elem)

    def handle_endtag(self, tag):
        if tag not in SELF_CLOSING:
            while len(self.stack) > 1:
                self.stack.pop()
                if tag == self.top.tag:
                    break

    def handle_data(self, data):
        if data != "":
            self.top.children.append(data)

    def error(self, message):
        # This method is undocumented in HTMLParser, but pylint is moaning
        # about it, so...
        logger.error("Error in Parser: %s", message)


def futz(markup):
    """
    Performs various kinds of cleanup on OEmbed data
    """
    parser = Parser()
    parser.feed(markup)

    width = 0
    height = 0
    for elem in parser.root:
        if isinstance(elem, str) or elem.tag != "iframe":
            continue
        elem.attrs["loading"] = "lazy"
        elem.attrs["sandbox"] = "allow-same-origin allow-scripts"
        for key in ["allowfullscreen", "allow"]:
            elem.attrs.pop(key, None)
        width = max(1, int(elem.attrs.get("width", "1")))
        # Fix undersized YT embeds
        if width < 560:
            height = max(1, int(elem.attrs.get("height", "1")))
            height = int(height * 560.0 / width)
            elem.attrs["height"] = str(height)
            width = 560
            elem.attrs["width"] = "560"

    with io.StringIO() as fh:
        parser.root.serialize(fh)
        return fh.getvalue(), width, height
