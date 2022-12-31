import re
from queue import Queue
from typing import Any

from discord import Intents, Client


class DiscommentClient(Client):
    def __init__(self, *, intents: Intents, msg_queue: Queue = None, **options: Any):
        super().__init__(intents=intents, **options)
        self.msg_queue = msg_queue

    @staticmethod
    def msg_to_json(msg) -> dict:
        content: str = msg.content
        content_body: str = content
        author: str = msg.author.display_name
        try:
            author, content_body = content.split("\n", 1)
            author_match = re.match("Author: .*", author)
            author: str = msg.author.display_name if author_match is None else author_match.string.split(":")[1].strip()
        except ValueError:
            pass
        return {"content": content_body, "author": author, "created_at": msg.created_at.isoformat(),
                "reactions": [{"emoji": r.emoji, "count": r.count} for r in msg.reactions]}

    def enqueue(self, msg):
        if self.msg_queue is None:
            return
        print(msg)
        self.msg_queue.put_nowait(msg)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        self.enqueue(message)

