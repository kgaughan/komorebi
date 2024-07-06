"""
XML utilities.
"""

import contextlib
import io
from xml.sax import saxutils


class XMLBuilder:
    """
    XML document builder. The code is purposely namespace ignorant: it's up to
    user to supply appropriate `xmlns` attributes as needed.

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
    """

    def __init__(self, out=None, encoding: str = "utf-8"):
        """
        `out` should be a file-like object to write the document to. If none
        is provided, a buffer is created.

        Note that if you provide your own, `as_string()` will return `None`
        as no other sensible value can be returned.
        """
        self.buffer = None
        if out is None:
            self.buffer = io.StringIO()
            out = self.buffer
        self.generator = saxutils.XMLGenerator(out, encoding)
        self.generator.startDocument()

    @contextlib.contextmanager
    def within(self, tag: str, **attrs):
        """
        Generates an element containing nested elements.
        """
        self.generator.startElement(tag, attrs)  # type: ignore
        yield
        self.generator.endElement(tag)

    def tag(self, tag: str, *values, **attrs):
        """
        Generates a simple element.
        """
        self.generator.startElement(tag, attrs)  # type: ignore
        for value in values:
            self.generator.characters(value)
        self.generator.endElement(tag)

    def __getattr__(self, tag: str):
        return lambda *values, **attrs: self.tag(tag, *values, **attrs)

    def append(self, other: str):
        """
        Append the string to this document.
        """
        self.generator.characters(other)
        return self

    def as_string(self) -> str:
        """
        If using the built-in buffer, get its current contents.
        """
        return "" if self.buffer is None else self.buffer.getvalue()

    def close(self):
        """
        If using the built-in buffer, clean it up.
        """
        if self.buffer is not None:
            self.buffer.close()
            self.buffer = None

    # Shortcuts.
    __iadd__ = append
    __str__ = as_string
