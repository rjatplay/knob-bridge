/******************************************************************
 * Quad-encoder → nRF24L01+  (QT Py RP2040)
 * Sends [zone, delta] for rotations, [zone|0x80, 0] for clicks.
 ******************************************************************/
#include <SPI.h>
#include "RF24.h"
#include "Adafruit_seesaw.h"
#include <seesaw_neopixel.h>

/* ─── nRF24 pins & settings ─────────────────────────────────── */
#define CE_PIN   29
#define CSN_PIN   5
const byte RF_ADDR[6] = "VOL01";
const uint8_t RF_CHANNEL = 90;

/* push-button GPIOs on Adafruit I²C Quad Rotary Encoder */
const uint8_t SW_PIN[4] = {12, 14, 17, 9};

RF24 radio(CE_PIN, CSN_PIN);

/* ─── Quad-encoder breakout (I2C) ───────────────────────────── */
#define SS_ADDR    0x49
#define SS_NEO_PIN 18
Adafruit_seesaw ss(&Wire);
seesaw_NeoPixel pixels(4, SS_NEO_PIN, NEO_GRB + NEO_KHZ800);
int32_t last_pos[4] = {0, 0, 0, 0};

/* ─── colour helper ─────────────────────────────────────────── */
uint32_t wheel(byte w) {
  w = 255 - w;
  if (w < 85)  return seesaw_NeoPixel::Color(255 - w * 3, 0, w * 3);
  if (w < 170) { w -= 85; return seesaw_NeoPixel::Color(0, w * 3, 255 - w * 3); }
  w -= 170;     return seesaw_NeoPixel::Color(w * 3, 255 - w * 3, 0);
}

void setup() {
  Serial.begin(115200);

  /* —— seesaw —— */
  if (!ss.begin(SS_ADDR) || !pixels.begin(SS_ADDR)) {
    Serial.println("Seesaw not found"); while (1);
  }
  for (int i = 0; i < 4; i++) {
    last_pos[i] = ss.getEncoderPosition(i);
    ss.enableEncoderInterrupt(i);

    ss.pinMode(SW_PIN[i], INPUT_PULLUP);        // enable pull-ups
    ss.setGPIOInterrupts(SW_PIN[i], true);      // ← fixed pin list
  }
  pixels.setBrightness(25);
  pixels.show();

  /* —— radio —— */
  if (!radio.begin()) { Serial.println("nRF24 fail"); while (1); }
  radio.setChannel(RF_CHANNEL);
  radio.setDataRate(RF24_1MBPS);
  radio.setPALevel(RF24_PA_LOW);
  radio.setPayloadSize(2);
  radio.openWritingPipe(RF_ADDR);
  radio.stopListening();

  Serial.println("TX-ENCODER ready");
}

void loop() {
  for (uint8_t z = 0; z < 4; z++) {

    /* ── rotary ─────────────────────────────────────────────── */
    int32_t pos  = ss.getEncoderPosition(z);
    int32_t diff = pos - last_pos[z];
    if (diff) {
      int8_t delta = diff;
      byte pkt[2]  = { z, (byte)delta };
      radio.write(pkt, 2);
      Serial.printf("Z%d Δ%d TX-ok\n", z, delta);

      pixels.setPixelColor(z, wheel(pos * 4));
      pixels.show();
      last_pos[z] = pos;
    }

    /* ── click ──────────────────────────────────────────────── */
    bool pressed = !ss.digitalRead(SW_PIN[z]);     // active-low
    static bool was_pressed[4] = { false };
    if (pressed && !was_pressed[z]) {              // rising edge
      byte pkt[2] = { (byte)(z | 0x80), 0 };       // mark click
      radio.write(pkt, 2);
      Serial.printf("Z%d click TX-ok\n", z);
    }
    was_pressed[z] = pressed;
  }
  delay(5);
}