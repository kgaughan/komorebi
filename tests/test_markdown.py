import unittest

from komorebi import formatting


class TestMarkdown(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(formatting.render_markdown(None), "")
        self.assertEqual(formatting.render_markdown(""), "")

    def test_basic_rendering(self):
        self.assertEqual(formatting.render_markdown("foo"), "<p>foo</p>")
