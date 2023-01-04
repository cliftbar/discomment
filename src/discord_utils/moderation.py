import logging
from profanity_check import predict_prob

from basic_log import log

wordlist: set[str] = set()


# TODO: more advanced algorithm
def wordlist_moderation(msg: str) -> bool:
    for word in wordlist:
        if word in msg:
            return False
    return True


def linear_moderation(msg: str, threshold: float = 0.4) -> bool:
    prob: float = predict_prob([msg])[0]
    log(f"linear moderation probability {prob}, threshold {threshold}", logging.DEBUG)
    return threshold < prob
