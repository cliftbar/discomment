from collections import deque
from typing import Optional

from discord import Message

from config import server_conf


class ChannelQueueManager:
    def __init__(self, queue_capacity: int = server_conf.msg_queue_max):
        self.queues: dict[int, deque[Message]] = {}
        self.queue_capacity: int = queue_capacity

    def get_queue(self, channel_id: int) -> deque[Message]:
        return self.queues.setdefault(channel_id, deque(maxlen=self.queue_capacity))

    def push(self, channel_id: int, item: Message):
        q = self.get_queue(channel_id)
        q.appendleft(item)

    def pop(self, channel_id: int, max_items: int = server_conf.msg_queue_fetch_limit, as_of: Optional[Message] = None):
        q = self.get_queue(channel_id)
        items: list[Message] = list(q)[:max_items]
        if as_of is not None:
            try:
                items_idx = items.index(as_of)
                items = items[:items_idx]
            except ValueError:
                pass
        items.reverse()
        return items
