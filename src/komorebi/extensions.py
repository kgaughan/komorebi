from flask_caching import Cache
from flask_compress import Compress

__all__ = [
    "cache",
    "compress",
]

cache = Cache()
compress = Compress()

# Set up cache for compressed responses.
compress.cache = cache
compress.cache_key = lambda request: request.url
