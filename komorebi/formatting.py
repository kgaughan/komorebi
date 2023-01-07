import markdown as md


def render_markdown(text):
    if text is None:
        return ""
    return md.markdown(
        text,
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
