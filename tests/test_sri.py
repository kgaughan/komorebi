from komorebi import sri

import io
import unittest


class TestSRI(unittest.TestCase):
    def test_binary(self):
        self.assertEqual(
            sri.generate_sri(io.BytesIO(b"abcedfg")),
            "sha384-3Kqax0ynJR7oxUL8wK8YhBgFkA4p8nENqXfWfgUfUG79JT5ad1YKCXH31y4zTCXH",
        )

    def test_text(self):
        """
        File should be opened as binary.
        """
        with self.assertRaises(TypeError):
            sri.generate_sri(io.StringIO("abcedfg"))
