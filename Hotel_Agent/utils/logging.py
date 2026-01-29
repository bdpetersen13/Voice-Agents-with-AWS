"""
Logging Utilities
Provides debug logging functionality
"""
import datetime
import inspect
from config.settings import get_config


def debug_print(message: str):
    """Print debug message with timestamp and function name"""
    config = get_config()
    if config.debug_mode:
        function_name = inspect.stack()[1].function
        if function_name == "time_it" or function_name == "time_it_async":
            function_name = inspect.stack()[2].function
        timestamp = "{:%Y-%m-%d %H:%M:%S.%f}".format(datetime.datetime.now())[:-3]
        print(f"{timestamp} {function_name} {message}")
