"""XML utilities."""

import contextlib
import io
from xml.sax import saxutils


class XMLBuilder:
    """An XML document builder.

    It's purposely namespace ignorant: it's up to user to supply appropriate
    `xmlns` attributes as needed.

    Examples:
        >>> xml = XMLBuilder()
        >>> with xml.within('root', xmlns='tag:talideon.com,2013:test'):
        ...     xml += 'Before'
        ...     with xml.within('leaf'):
        ...         xml += 'Within'
        ...     xml += 'After'
        ...     xml.tag('leaf', 'Another')
        >>> print xml.as_string()
        <?xml version="1.0" encoding="utf-8"?>
        <root xmlns="tag:talideon.com,2013:test">Before<leaf>Within</leaf>After<leaf>Another</leaf></root>

    Args:
        out: a file-like object to write the document to; if none is provided,
            a buffer is created.

    Note:
        If you provide your own, the `as_string()` method will return an empty
        string as no other sensible value can be returned.
    """

    def __init__(self, out: io.IOBase | None = None, encoding: str = "utf-8") -> None:
        self.buffer = None
        if out is None:
            self.buffer = io.StringIO()
            out = self.buffer
        self.generator = saxutils.XMLGenerator(out, encoding)
        self.generator.startDocument()

    @contextlib.contextmanager
    def within(self, tag: str, **attrs: str):
        """Generates an element containing nested elements.

        Args:
            tag: the tag name
            attrs: any attributes to add to the tag
        """
        self.generator.startElement(tag, attrs)  # type: ignore
        yield
        self.generator.endElement(tag)

    def tag(self, tag: str, *values: str, **attrs: str) -> None:
        """Generates a simple element.

        Args:
            tag: the tag name
            values: any character data to write between the start and end tag
            attrs: any attributes to add to the tag
        """
        self.generator.startElement(tag, attrs)  # type: ignore
        for value in values:
            self.generator.characters(value)
        self.generator.endElement(tag)

    def __getattr__(self, tag: str):
        return lambda *values, **attrs: self.tag(tag, *values, **attrs)

    def append(self, other: str) -> "XMLBuilder":
        """Append the string to this document.

        Args:
            other: a string to write to the document
        """
        self.generator.characters(other)
        return self

    def as_string(self) -> str:
        """If using the built-in buffer, get its current contents."""
        return "" if self.buffer is None else self.buffer.getvalue()

    def close(self) -> None:
        """If using the built-in buffer, clean it up."""
        if self.buffer is not None:
            self.buffer.close()
            self.buffer = None

    # Shortcuts.
    __iadd__ = append
    __str__ = as_string
