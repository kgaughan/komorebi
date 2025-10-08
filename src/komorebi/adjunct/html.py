"""
HTML parsing and serialisation support.
"""

import dataclasses
from html import escape
from html.parser import HTMLParser
import io
import logging
import typing as t

logger = logging.getLogger(__name__)

__all__ = [
    "Element",
    "Parser",
    "escape",
]

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


def make(
    tag: str,
    attrs: t.Mapping[str, str | None],
    *,
    close: bool | None = None,
) -> str:
    """
    Helper for quickly constructing a HTML tag.
    """
    attr_list = []
    for name, value in attrs.items():
        if value is None:
            attr_list.append(f" {name}")
        else:
            attr_list.append(f' {name}="{escape(value, quote=True)}"')
    result = f"<{tag}{''.join(attr_list)}>"
    if close is None:
        close = tag not in SELF_CLOSING
    if close:
        result += f"</{tag}>"
    return result


@dataclasses.dataclass
class Element:
    tag: str | None
    attrs: dict = dataclasses.field(default_factory=dict)
    children: list = dataclasses.field(default_factory=list)

    def __getitem__(self, i: int):
        return self.children[i]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def serialize(self, dest: io.TextIOBase | None = None) -> io.TextIOBase:
        if dest is None:
            dest = io.StringIO()
        if self.tag is not None:
            dest.write(f"<{self.tag}")
            for key, value in self.attrs.items():
                dest.write(f" {key}")
                if value is not None:
                    dest.write('="' + escape(value, quote=True) + '"')
            dest.write(">")
        for child in self.children:
            if isinstance(child, str):
                dest.write(escape(child, quote=False))
            elif isinstance(child, Element):
                child.serialize(dest)
        if self.tag is not None and self.tag not in SELF_CLOSING:
            dest.write(f"</{self.tag}>")

        return dest


class Parser(HTMLParser):
    """
    Parses a HTML document into
    """

    def __init__(self) -> None:
        super().__init__()
        self.root = Element(tag=None)
        self.stack = [self.root]

    @property
    def top(self):
        return self.stack[-1]

    def handle_starttag(self, tag, attrs) -> None:
        elem = Element(tag=tag, attrs=dict(attrs))
        self.top.children.append(elem)
        if tag not in SELF_CLOSING:
            self.stack.append(elem)

    def handle_startendtag(self, tag, attrs) -> None:
        elem = Element(tag=tag, attrs=dict(attrs))
        self.top.children.append(elem)

    def handle_endtag(self, tag) -> None:
        if tag not in SELF_CLOSING:
            while len(self.stack) > 1:
                self.stack.pop()
                if tag == self.top.tag:
                    break

    def handle_data(self, data) -> None:
        if data != "":
            self.top.children.append(data)

    def error(self, message: str) -> None:
        # This method is undocumented in HTMLParser, but pylint is moaning
        # about it, so...
        logger.error("Error in Parser: %s", message)  # pragma: no cover


def parse(markup: str) -> Element:
    parser = Parser()
    parser.feed(markup)
    parser.close()
    return parser.root
