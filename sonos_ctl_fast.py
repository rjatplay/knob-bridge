#!/usr/bin/env python3
import soco, socket
from functools import lru_cache

socket.setdefaulttimeout(2)                      # <— 2-s network timeout

SPEAKERS = {                                     # ← put real IPs here
    "shelf":   "192.168.0.119",
    "bedroom": "192.168.0.150",
}

@lru_cache(maxsize=None)
def _spk(name):                                  # memoised connector
    return soco.SoCo(SPEAKERS[name])

def bump(name, delta):
    """Change volume; fail quietly if the speaker is off-line."""
    try:
        spk  = _spk(name)
        new  = max(0, min(100, spk.volume + int(delta)))
        spk.volume = new
        return new
    except (soco.SoCoException, OSError, socket.timeout):
        return 0                                 # silent ignore
