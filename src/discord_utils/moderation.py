import logging

from profanity_check import predict_prob

from basic_log import log
from config import account_conf

wordlist: set[str] = set()


def validate_msg(msg: str, max_length: int = account_conf.max_msg_length,
                 moderation_threshold: float = account_conf.linear_moderation_threshold) -> bool:
    return linear_moderation(msg, moderation_threshold) and len(msg) < max_length


# TODO: more advanced algorithm
def wordlist_moderation(msg: str) -> bool:
    for word in wordlist:
        if word in msg:
            return False
    return True


def linear_moderation(msg: str, threshold: float) -> bool:
    prob: float = predict_prob([msg])[0]
    log(f"linear moderation probability {prob}, threshold {threshold}", logging.DEBUG)
    return threshold < prob
