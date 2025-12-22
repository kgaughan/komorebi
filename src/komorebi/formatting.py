import contextvars

import markdown

_formatter: contextvars.ContextVar[markdown.Markdown] = contextvars.ContextVar("_formatter")


def render_markdown(text: str | None) -> str:
    if text is None:
        return ""
    try:
        formatter = _formatter.get()
    except LookupError:
        formatter = markdown.Markdown(
            output_format="html",
            extensions=[
                "smarty",
                "tables",
                "attr_list",
                "def_list",
                "fenced_code",
                "admonition",
            ],
        )
        _formatter.set(formatter)
    return formatter.reset().convert(text)
