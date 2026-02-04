import logging

logger = logging.getLogger("digicpu")

def setup():
    logger = logging.getLogger("digicpu")
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)

    try:
        from digiformatter import logger as digilogger
        dfhandler = digilogger.DigiFormatterHandler()
        logger.handlers = []
        logger.propagate = False
        logger.addHandler(dfhandler)
    except ImportError:
        pass
