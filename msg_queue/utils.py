from queue import Empty, Queue

from dctypes import T


def queue_get_many(q: Queue[T], max_items: int = 10) -> list[T]:
    items: list[T] = []
    for numOfItemsRetrieved in range(0, max_items):
        try:
            if numOfItemsRetrieved == max_items:
                break
            items.append(q.get_nowait())
            print(items)
        except Empty:
            break
    return items
