import typing as t


def parse_header(line: str) -> tuple[str, dict[str, str]]:
    """Parse HTTP headers with the same format as `Content-Type`.

    Args:
        line: a HTTP header line

    Returns:
        The main value and a dictionary of options.

    (Copied from Python's `cgi` module until I can find a better alternative.)
    """
    parts = _parseparam(f";{line}")
    key = parts.__next__()
    pdict = {}
    for part in parts:
        i = part.find("=")
        if i >= 0:
            name = part[:i].strip().lower()
            value = part[i + 1 :].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace("\\\\", "\\").replace('\\"', '"')
            pdict[name] = value
    return key, pdict


def _parseparam(seg: str) -> t.Iterator[str]:
    while seg[:1] == ";":
        seg = seg[1:]
        end = seg.find(";")
        while end > 0 and (seg.count('"', 0, end) - seg.count('\\"', 0, end)) % 2:
            end = seg.find(";", end + 1)
        if end < 0:
            end = len(seg)
        field = seg[:end]
        yield field.strip()
        seg = seg[end:]
