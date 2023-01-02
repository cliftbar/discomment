import logging
from queue import Empty, Queue

from basic_log import log
from config import server_conf
from dctypes import T


def queue_get_many(q: Queue[T], max_items: int = server_conf.msg_queue_max) -> list[T]:
    items: list[T] = []
    for numOfItemsRetrieved in range(0, max_items):
        try:
            if numOfItemsRetrieved == max_items:
                break
            items.append(q.get_nowait())
            log(str(items), logging.DEBUG)
        except Empty:
            break
    return items
