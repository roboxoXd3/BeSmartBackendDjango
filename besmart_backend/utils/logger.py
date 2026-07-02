import structlog

def get_logger(name=None):
    """
    Returns a configured structlog logger.
    Use this across the codebase to ensure consistent structured logging.
    """
    return structlog.get_logger(name)
