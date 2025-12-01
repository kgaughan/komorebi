import contextlib
import logging
import os
import sys
from wsgiref import simple_server

from .app import create_wsgi_app

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)

logger = logging.getLogger(__name__)

# Check whether the configuration is in the environment
if "KOMOREBI_SETTINGS" not in os.environ:
    sys.exit("error: KOMOREBI_SETTINGS cannot be found in the environment")
if not os.path.isabs(os.environ["KOMOREBI_SETTINGS"]):
    logger.warning("KOMOREBI_SETTINGS should be an absolute path: expect strangeness!")

with simple_server.make_server("", 8000, create_wsgi_app()) as svr, contextlib.suppress(KeyboardInterrupt):
    logger.info("Running on http://localhost:8000...")
    svr.serve_forever()
