import logging
from logging.handlers import TimedRotatingFileHandler
import re
import sys

# Define a pattern to exclude from logs and stdout
EXCLUDE_PATTERN = re.compile(r'secret|password', re.IGNORECASE)
PRINT_PATTERN = re.compile(r'print|save', re.IGNORECASE)

# Function to create a handler for a specific log level and file
def create_handler(filename, level):
    handler = TimedRotatingFileHandler(filename, when='midnight', interval=1, backupCount=5)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
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

# Override the built-in print function
python_original_print = print
def print(*args, **kwargs):
    # Convert all arguments to string and concatenate them
    message = ' '.join(map(str, args))
    # Check if the message contains the excluded pattern
    if not EXCLUDE_PATTERN.search(message):
        # If it doesn't contain the pattern, log the message and print it
        if PRINT_PATTERN.search(message):
            python_original_print(message, **kwargs)
        else:
            logger.info(message)  # Adjust the logging level if necessary
    # If the pattern is found, neither log nor print the message

sys.stdout.write = print

