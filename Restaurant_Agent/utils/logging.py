"""
Logging Utilities
Debug printing with timestamps and function names
"""
import inspect
import datetime
from config.settings import get_config


def debug_print(message):
    """Print only if debug mode is enabled"""
    config = get_config()
    if config.debug_mode:
        function_name = inspect.stack()[1].function
        if function_name == "time_it" or function_name == "time_it_async":
            function_name = inspect.stack()[2].function
        timestamp = "{:%Y-%m-%d %H:%M:%S.%f}".format(datetime.datetime.now())[:-3]
        print(f"{timestamp} {function_name} {message}")
