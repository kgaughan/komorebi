"""
An intensely pragmatic implementation of the Open Graph Protocol.

This follows `the specification <https://opengraphprotocol.org/>`_ rather than
attempting to implement RDFa.

# Theory of Operation

The metadata consists of a list of properties. A property may be unstructured
(a string) or structured (a list of properties). A property may appear more
than once. Properties has the form "ns:name", while a metadata field to be
attached to a property (thus making it structured) has the form "ns:name:meta".

Metadata should be implemented as a multimap, but I'll be treating it as a map.

Example of prefix with multiple entries:
<body prefix="dc: http://purl.org/dc/terms/ schema: http://schema.org/">

If this is present: vocab="http://www.w3.org/2011/rdfa-context/rdfa-1.1"
An initial context is set up consisting of the namespaces given on that page.
"""

import dataclasses
import html
import typing as t


@dataclasses.dataclass
class Property:
    type_: str
    value: str
    metadata: t.Dict[str, str]

    def to_meta(self) -> str:
        lines = [
            f'<meta property="og:{html.escape(self.type_)}" content="{html.escape(self.value)}">',
        ]
        lines.extend(
            f'<meta property="og:{html.escape(self.type_)}:{html.escape(key)}" content="{html.escape(value)}">'
            for key, value in self.metadata.items()
        )
        return "\n".join(lines)


def parse(properties: t.Collection[t.Tuple[str, str]]) -> t.Sequence[Property]:
    result = []
    for name, value in properties:
        name_parts = name.split(":", 2)
        if len(name_parts) == 2:
            result.append(Property(name_parts[1], value, {}))
        if len(name_parts) == 3:
            # Skip any bad metadata
            if not result or result[-1].type_ != name_parts[1]:
                continue
            result[-1].metadata[name_parts[2]] = value
    return result


def to_meta(props: Property | t.Sequence[Property]) -> str:
    if isinstance(props, Property):
        return props.to_meta()
    return "\n".join(prop.to_meta() for prop in props)


def find(
    props: t.Sequence[Property],
    type_: str,
    value: str | None = None,
) -> t.Iterable[Property]:
    for prop in props:
        if prop.type_ == type_ and (value is None or prop.value == value):
            yield prop
