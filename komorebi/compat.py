def parse_header(line):
    """
    Parse a Content-type like header.

    Return the main content-type and a dictionary of options.

    Copied, with _parseparam, from Python's cgi module until I can find a
    better alternative.
    """
    parts = _parseparam(";" + line)
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


def _parseparam(seg):
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
