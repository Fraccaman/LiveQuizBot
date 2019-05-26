from multiprocessing.pool import ThreadPool
from typing import Callable, List, Any


def parallel_execution(pool: ThreadPool, func: Callable, data: List) -> List[Any]:
    return pool.map(func, data)
