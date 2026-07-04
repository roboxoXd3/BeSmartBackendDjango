import logging
from besmart_backend.settings import LOGGING
import logging.config

logging.config.dictConfig(LOGGING)

logger = logging.getLogger("django")
logger.info("Test log from standard python logger")

