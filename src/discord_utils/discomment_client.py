import logging
import re
from typing import Any

from discord import Intents, Client, Message

from basic_log import log
from msg_queue import ChannelQueueManager


class DiscommentClient(Client):
    def __init__(self, *, intents: Intents, msg_manager: ChannelQueueManager = None, **options: Any):
        super().__init__(intents=intents, **options)
        self.msg_manager: ChannelQueueManager = msg_manager

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

    def enqueue(self, msg: Message):
        if self.msg_manager is None:
            return
        log(str(msg), logging.DEBUG)
        self.msg_manager.push(msg.channel.id, msg)

    async def on_ready(self):
        log(f"Logged on as {self.user}!", logging.INFO)

    async def on_message(self, message):
        log(f"Message from {message.author}: {message.content}", logging.INFO)
        self.enqueue(message)
