from queue import Queue

from config import server_conf

msg_queue: Queue = Queue(maxsize=server_conf.msg_queue_max)
