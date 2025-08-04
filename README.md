Here’s the full README.md written in proper Markdown — you can copy and paste this directly into ~/knob-bridge/README.md on your Pi.

⸻


# Knob-Bridge — Denon & Sonos Volume Remote

Four rotary encoders on an Adafruit **I²C Quad Rotary Encoder** board send
2-byte NRF24 packets to a Raspberry Pi.  
The Pi translates each packet into a volume bump for:

| Encoder | Target            | Command format          |
|---------|-------------------|-------------------------|
| **0**   | Denon main zone   | `MVUP / MVDOWN`         |
| **1**   | Denon Zone-2      | `Z2UP / Z2DOWN`         |
| **2**   | Sonos “shelf”     | SoCo volume             |
| **3**   | Sonos “bedroom”   | SoCo volume             |

> **Note:** Push-button clicks are disabled for now.  
> Sonos calls fail quietly — if a speaker is offline, the bridge pauses ≤2 seconds and continues running.

---

## File layout

| File               | Description |
|--------------------|-------------|
| `knob_bridge.py`   | Main loop — reads NRF24 packets, batches deltas, and routes to the right system |
| `denon_sock.py`    | Telnet helper for Denon — exposes `bump_denon(delta, zone)` |
| `sonos_ctl_fast.py`| SoCo-based helper — exposes `bump(name, delta)` with timeout handling |
| `encoder_tx.ino`   | QT Py sketch — reads encoders and sends NRF24 packets (`zone`, `delta`) |

---

## Hardware

| Component            | Details |
|----------------------|---------|
| **Rotary Encoder Board** | Adafruit I²C Quad Encoder (A0 = 0x49), button pins: 12 / 14 / 17 / 9 |
| **RF Radio**         | NRF24L01+ (CE = GPIO 25, CSN = CE0) |
| **Controller**       | Raspberry Pi (any model with SPI enabled) |
| **Denon AVR**        | IP: `192.168.0.102` (Telnet on port 23) |
| **Sonos speakers**   | “shelf” = `192.168.0.119`, “bedroom” = `192.168.0.150` |

*Edit those IPs/pins in the Python scripts as needed.*

---

## Quick start (on the Pi)

```bash
# One-time setup
sudo apt update
sudo apt install -y pigpio python3-pip git
python3 -m pip install --break-system-packages nrf24 soco

# Enable pigpio daemon
sudo systemctl enable --now pigpiod

# Run the bridge
python3 knob_bridge.py   # Ctrl-C to quit


⸻

Troubleshooting

Symptom	Fix
Encoder 1 (Zone-2) volume lags	In denon_sock.py: set _VOL_DELAY = 0.02 and avoid redundant Z2ON calls
Encoder 1 doesn’t work at all	Check if zone=2 in packets — update pending[2] block if needed
Sonos traceback / crash	Use the updated sonos_ctl_fast.py with try/except and socket.setdefaulttimeout(2)
Sonos knob unresponsive	Check IP in SPEAKERS; confirm speaker is powered on and not grouped/muted
pigpio.error: 'no handle available'	Run sudo systemctl restart pigpiod


⸻

Git workflow (local + GitHub)

# Initialize once
git init

# Track all project files
git add knob_bridge.py denon_sock.py sonos_ctl_fast.py encoder_tx.ino README.md
git commit -m "Working: Denon + Sonos volume; no buttons yet"

# Push to GitHub
git remote add origin git@github.com:your-username/knob-bridge.git
git branch -M main
git push -u origin main

After edits

git add .
git commit -m "Short description of what changed"
git push

Rollback example

git log --oneline
git checkout <commit-hash> -- knob_bridge.py


⸻

To-do / planned
	•	Re-enable click-based mute / play/pause actions
	•	Replace per-detent bursts with absolute volume command (MV65, Z275, etc)
	•	Auto-detect AirPlay/HEOS target and route clicks dynamicallyy

