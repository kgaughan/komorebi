import base64
import hashlib
import io


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
