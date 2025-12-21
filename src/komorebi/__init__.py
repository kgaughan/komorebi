from .app import create_app, create_wsgi_app

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0-dev"


__all__ = [
    "__version__",
    "create_app",
    "create_wsgi_app",
]
