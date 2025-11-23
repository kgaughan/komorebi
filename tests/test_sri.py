import io

from komorebi import sri


def test_binary():
    assert (
        sri.generate_sri(io.BytesIO(b"abcedfg"))
        == "sha384-3Kqax0ynJR7oxUL8wK8YhBgFkA4p8nENqXfWfgUfUG79JT5ad1YKCXH31y4zTCXH"
    )
