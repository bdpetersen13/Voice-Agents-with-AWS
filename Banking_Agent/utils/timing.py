"""
Performance Timing Utilities
"""
import time
from utils.logging import debug_print


def time_it(label: str, methodToRun):
    """Time a synchronous function execution"""
    start_time = time.perf_counter()
    result = methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


async def time_it_async(label: str, methodToRun):
    """Time an asynchronous function execution"""
    start_time = time.perf_counter()
    result = await methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result
