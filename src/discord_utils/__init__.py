from discord import Intents

from discord_utils.discomment_client import DiscommentClient
from msg_queue import msg_queue

intents = Intents.default()
intents.message_content = True
discord_client: DiscommentClient = DiscommentClient(intents=intents, msg_queue=msg_queue)
