#!/usr/bin/env python3
"""
denon_sock.py – lean Telnet helper for Denon / Marantz AVRs
Only what you need for rotary volume (no button transport code)
"""

import socket, time

DENON_IP   = "192.168.0.102"   # ← put your AVR’s IP here
DENON_PORT = 23
SO_TIMEOUT = 1.0               # seconds

# ── low-level socket wrapper ────────────────────────────────────
class _Sock:
    def __init__(self):
        self.s = None
    def _connect(self):
        if self.s:
            return
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(SO_TIMEOUT)
        self.s.connect((DENON_IP, DENON_PORT))
    def send(self, cmd: str):
        self._connect()
        self.s.sendall((cmd + "\r").encode())
        try:
            self.s.recv(64)    # ignore echo
        except socket.timeout:
            pass

DENON = _Sock()

# ── volume helper ───────────────────────────────────────────────
_VOL_DELAY = 0.02          # 20 ms between UP/DOWN packets
_zone_awake = {0: True, 2: False, 3: False}  # remember if ON already

def bump_denon(delta: int, *, zone: int = 0):
    """
    ±1 detent ⇒ ±0.5 dB
      zone 0 → main (MVUP/MVDOWN)
      zone 2 → Zone-2 (Z2UP/Z2DOWN)
    """
    global _zone_awake
    if delta == 0:
        return

    prefix = "MV" if zone == 0 else f"Z{zone}"

    # Wake Zone-2 / Zone-3 only once per power-cycle
    if zone and not _zone_awake[zone]:
        DENON.send(f"{prefix}ON")
        _zone_awake[zone] = True

    up, dn = f"{prefix}UP", f"{prefix}DOWN"
    for _ in range(abs(delta)):
        DENON.send(up if delta > 0 else dn)
        time.sleep(_VOL_DELAY)
