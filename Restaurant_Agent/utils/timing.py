"""
Timing Utilities
Performance measurement decorators
"""
import time
from utils.logging import debug_print


def time_it(label, method_to_run):
    """Time a synchronous function execution"""
    start_time = time.perf_counter()
    result = method_to_run()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


async def time_it_async(label, method_to_run):
    """Time an asynchronous function execution"""
    start_time = time.perf_counter()
    result = await method_to_run()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result
