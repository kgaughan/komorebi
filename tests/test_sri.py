import io

import pytest

from komorebi import sri


def test_binary():
    assert (
        sri.generate_sri(io.BytesIO(b"abcedfg"))
        == "sha384-3Kqax0ynJR7oxUL8wK8YhBgFkA4p8nENqXfWfgUfUG79JT5ad1YKCXH31y4zTCXH"
    )


def test_text():
    # File should be opened as binary
    with pytest.raises(TypeError):
        sri.generate_sri(io.StringIO("abcedfg"))
