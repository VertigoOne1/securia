#!/bin/python3

## Logger configuration settings and routines

import logging, sys, os
from envyaml import EnvYAML

config = EnvYAML('config.yml')

DEBUG_LEVEL = str(config['general']['default_debug_level']).upper()

logging.lastResort = None

def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

def setup_custom_logger(name):
    print(f"--- Setup custom logger - {name} ---")
    try:
        addLoggingLevel('TRACE', logging.DEBUG - 5)
    except:
        pass
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-4s %(name)s %(funcName)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

    logger2 = logging.getLogger()
    logger = logging.getLogger(name)
    defaultlevel = logging.getLevelName(DEBUG_LEVEL)
    logger.setLevel(defaultlevel)

    if config["logging"]["enable_stdout_log_handler"]:
        screen_handler = logging.StreamHandler(stream=sys.stdout)
        screen_handler.setFormatter(formatter)
        logger.addHandler(screen_handler)
        logger.propagate = False
        logger.info("Default stdout logging handler enabled")
    else:
        logger.info("Default stdout logging handler disabled")

    if config["logging"]["enable_file_log_handler"]:
        file_handler = logging.FileHandler('/data/log.txt', mode='w')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info("File logging handler enabled")
    else:
        logger.info("File logging handler disabled")

    logging.info("Logging setup complete, disable further root logger messages that is not CRITICAL level")
    logger2 = None
    logger.propagate = False
    return logger