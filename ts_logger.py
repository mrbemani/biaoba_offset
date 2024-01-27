# Description: This file contains the code to create a logger that will log to a file
#              based on the log level. The log files will be rotated daily and will
#              be kept for 5 days.
# Author:      Mr.Bemani
# Date:        2019-12-20
# Usage:       from ts_logger import logger
#              logger.debug('This is a debug message')
#              logger.info('This is an info message')
#              logger.warning('This is a warning message')
#              logger.error('This is an error message')
#              logger.critical('This is a critical message')
#

__author__ = 'Mr.Bemani'

import logging
from logging.handlers import TimedRotatingFileHandler

# Function to create a handler for a specific log level and file
def create_handler(filename, level):
    handler = TimedRotatingFileHandler(filename, when='midnight', interval=1, backupCount=5)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s')
    handler.setFormatter(formatter)
    return handler

# Create the base logger
logger = logging.getLogger('my_daily_logger')
logger.setLevel(logging.DEBUG)  # Capture all levels of log messages

# Create handlers for different log levels
handlers = {
    logging.DEBUG: create_handler('debug_daily.log', logging.DEBUG),
    logging.INFO: create_handler('info_daily.log', logging.INFO),
    logging.WARNING: create_handler('warning_daily.log', logging.WARNING),
    logging.ERROR: create_handler('error_daily.log', logging.ERROR),
    logging.CRITICAL: create_handler('critical_daily.log', logging.CRITICAL),
}

# Add handlers to the logger
for handler in handlers.values():
    logger.addHandler(handler)
