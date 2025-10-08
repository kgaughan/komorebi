
from komorebi import formatting


def test_empty():
    assert formatting.render_markdown(None) == ""
    assert formatting.render_markdown("") == ""


def test_basic_rendering():
    assert formatting.render_markdown("foo") == "<p>foo</p>"
