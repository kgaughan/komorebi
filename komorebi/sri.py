import base64
import hashlib
import io
import json
import os
from typing import Dict

import click

# File extensions to generate SRI hashes for
SUFFIXES = (
    ".css",
    ".js",
)


def generate_sri(
    fh: io.BufferedReader,
    alg: str = "sha384",
    block_size: int = 8192,
) -> str:
    """
    A basic [subresource integrity](https://www.w3.org/TR/SRI/) hashing
    implementation. This doesn't check the algorithm chosen nor does it support
    multiple algorithms.
    """
    hashed = hashlib.new(alg)
    while True:
        blk = fh.read(block_size)
        if not blk:
            break
        hashed.update(blk)
    digest = base64.b64encode(hashed.digest()).decode("UTF-8")
    return f"{alg}-{digest}"


def load_sris() -> Dict[str, str]:
    sris_path = os.path.join(os.path.dirname(__file__), "sri.json")
    if not os.path.exists(sris_path):
        return {}
    with open(sris_path, "r", encoding="UTF-8") as fh:
        return json.load(fh)


@click.command("sri", help="Generate SRI cache")
def generate_hashes():
    app_root = os.path.dirname(__file__)
    static_root = os.path.join(app_root, "static")
    hashes = {}
    for root, _, files in os.walk(static_root):
        for filename in files:
            if filename.endswith(SUFFIXES):
                filepath = os.path.join(root, filename)
                with open(filepath, "rb") as fh:
                    hashes[filepath[len(static_root) + 1 :]] = generate_sri(fh)
    with open(os.path.join(app_root, "sri.json"), "w", encoding="UTF-8") as fh:
        json.dump(hashes, fh, indent=2, sort_keys=True)
        fh.write("\n")
