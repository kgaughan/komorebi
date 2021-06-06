"""
An intensely pragmatic implementation of the Open Graph Protocol.

This follows `the specification <https://opengraphprotocol.org/>`_ rather than
attempting to implement RDFa.

In spite of the name, it's really just a tree with named edges.
"""

import collections
import html


class SingleValue:

    __slots__ = [
        "content",
        "attrs",
    ]

    def __init__(self, content=None):
        self.content = content
        self.attrs = collections.defaultdict(SingleValue)

    def append(self, content):
        if self.content is None:
            self.content = content
            return self
        return MultiValue(self, content)

    def __len__(self):
        return 1

    def __str__(self):
        return self.content

    def __iter__(self):
        return iter([self])

    def flatten(self):
        for key, value in self.attrs.items():
            for pair in value._flatten(key):
                yield pair

    def to_meta(self):
        return "\n".join(
            f'<meta property="{html.escape(key)}" content="{html.escape(value)}">'
            for key, value in self.flatten()
        )

    def _flatten(self, prefix):
        if self.content is not None:
            yield (prefix, self.content)
        for key, value in self.attrs.items():
            for pair in value._flatten(prefix + ":" + key):
                yield pair


class MultiValue:

    __slots__ = [
        "_values",
    ]

    def __init__(self, orig, appended):
        self._values = [orig]
        self.append(appended)

    def append(self, content):
        self._values.append(SingleValue(content))
        return self

    def __len__(self):
        return len(self._values)

    def __str__(self):
        return ", ".join(self._values)

    def __iter__(self):
        return iter(self._values)

    @property
    def attrs(self):
        return self._values[-1].attrs

    def _flatten(self, prefix):
        for value in self._values:
            for pair in value._flatten(prefix):
                yield pair


class Root(SingleValue):
    def insert(self, prop, content):
        """
        Break apart a property name and insert the content into the 'graph'.
        """
        prev = None
        node = self
        key = None  # Keep pylint happy
        for key in prop.split(":"):
            prev, node = node, node.attrs[key]
        # This is safe: there will always be at least one previous node, namely
        # the root.
        prev.attrs[key] = node.append(content)

    def get_all(self, prop):
        node = self
        for key in prop.split(":"):
            node = node.attrs[key]
        for item in node:
            yield item

    def get(self, prop) -> SingleValue:
        last = None
        for item in self.get_all(prop):
            last = item
        return last

    def __str__(self):
        return self.to_meta()

    @classmethod
    def from_list(cls, lst):
        root = cls()
        for prop, content in lst:
            root.insert(prop, content)
        return root
