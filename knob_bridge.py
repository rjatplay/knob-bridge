#!/usr/bin/env python3
"""
knob_bridge.py – nRF24 → Denon + Sonos volume bridge
  Encoder 0 → Denon main zone
  Encoder 1 → Denon Zone-2
  Encoder 2 → Sonos “shelf”
  Encoder 3 → Sonos “bedroom”
(No button handling for now)
"""

import time, struct, pigpio
from nrf24 import NRF24, RF24_DATA_RATE

from denon_sock       import bump_denon
from sonos_ctl_fast   import bump as bump_sonos   # <— Sonos back on

# ── RF24 wiring & params ───────────────────────────────────────
CE_PIN  = 25              # GPIO 25 (pin 22)
SPI_CH  = 0               # CE0     (pin 24)
ADDR    = b"VOL01"
CHANNEL = 90

pi = pigpio.pi()
radio = NRF24(pi, CE_PIN, SPI_CH)
radio.set_payload_size(2)
radio.set_channel(CHANNEL)
radio.set_data_rate(RF24_DATA_RATE.RATE_1MBPS)
radio.open_reading_pipe(0, ADDR)
radio.listen = True

# ── accumulators & timing ──────────────────────────────────────
pending    = [0, 0, 0, 0]      # enc0-enc3
FLUSH_SEC  = 0.04              # 40 ms batch window (snappy)
last_flush = time.monotonic()

def flush():
    global last_flush
    if pending[0]:
        bump_denon(pending[0], zone=0)        # main
        pending[0] = 0
    if pending[1]:
        bump_denon(pending[1], zone=2)        # Zone-2
        pending[1] = 0
    if pending[2]:
        bump_sonos("shelf", pending[2])       # Sonos shelf
        pending[2] = 0
    if pending[3]:
        bump_sonos("bedroom", pending[3])     # Sonos bedroom
        pending[3] = 0
    last_flush = time.monotonic()

print("RF bridge running … Ctrl-C to quit")
try:
    while True:
        while radio.data_ready():
            zone, delta = struct.unpack("Bb", bytes(radio.get_payload()))
            if 0 <= zone <= 3:
                pending[zone] += delta

        if time.monotonic() - last_flush > FLUSH_SEC:
            flush()

        time.sleep(0.005)

except KeyboardInterrupt:
    print("\nbye.")
finally:
    pi.stop()
