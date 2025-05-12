import asyncio
from typing import Any, Callable


def create_queue(maxsize: int = 0) -> asyncio.Queue[Any]:
    """
    Create and return an asyncio.Queue with optional maxsize.

    Args:
        maxsize: maximum number of items that can be queued before put() blocks. 0 means infinite.

    Returns:
        An asyncio.Queue instance.
    """
    return asyncio.Queue(maxsize=maxsize)


def start_workers(
    queue: asyncio.Queue[Any],
    worker_fn: Callable[[asyncio.Queue[Any], Any], Any],
    client: Any,
    worker_count: int = 5
) -> None:
    """
    Spawn multiple worker tasks consuming from the queue.

    Args:
        queue: The asyncio.Queue from which to retrieve work items.
        worker_fn: A coroutine function with signature (queue, client) to process items.
        client: The API client or context object to pass to each worker.
        worker_count: The number of concurrent worker tasks to launch.
    """
    for _ in range(worker_count):
        asyncio.create_task(worker_fn(queue, client))


def enqueue_item(queue: asyncio.Queue[Any], item: Any) -> None:
    """
    Put an item into the queue without blocking.

    Args:
        queue: The asyncio.Queue to enqueue into.
        item: The work item to add.
    """
    queue.put_nowait(item)


async def wait_for_completion(queue: asyncio.Queue[Any]) -> None:
    """
    Wait until all items in the queue have been processed (i.e., task_done() called for each item).

    Args:
        queue: The asyncio.Queue to monitor.
    """
    await queue.join()
