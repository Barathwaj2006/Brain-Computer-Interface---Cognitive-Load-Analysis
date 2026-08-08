/*
 * NEUROSIM — Synthetic EEG ESP32 DevKit V1 Firmware
 *
 * Hardware Connections:
 * P1 (Delta Component Control) -> GPIO 34 (ADC1_CH6)
 * P2 (Theta Component Control) -> GPIO 35 (ADC1_CH7)
 * P3 (Alpha Component Control) -> GPIO 32 (ADC1_CH4)
 * P4 (Beta Component Control)  -> GPIO 33 (ADC1_CH5)
 *
 * Baud Rate: 115200
 * Target Sampling Rate: 250 Hz (4000 microsecond timer loop)
 *
 * Output Stream Format:
 * SAMPLE,<waveform_microvolts>,<sequence_number>,<checksum>
 */

#include <Arduino.h>

// ADC Pin Assignments
const int PIN_POT_DELTA = 34;
const int PIN_POT_THETA = 35;
const int PIN_POT_ALPHA = 32;
const int PIN_POT_BETA  = 33;

// Frequencies (Hz)
const float FREQ_DELTA = 2.0;
const float FREQ_THETA = 6.0;
const float FREQ_ALPHA = 10.0;
const float FREQ_BETA  = 20.0;

// Sampling Config
const unsigned long SAMPLE_INTERVAL_US = 4000; // 250 Hz = 4000 microseconds
unsigned long lastSampleTime = 0;
float timeSeconds = 0.0;
unsigned long sequenceNumber = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_POT_DELTA, INPUT);
  pinMode(PIN_POT_THETA, INPUT);
  pinMode(PIN_POT_ALPHA, INPUT);
  pinMode(PIN_POT_BETA, INPUT);

  // Configure ADC resolution
  analogReadResolution(12); // 0 - 4095
  delay(500);

  // Initial Handshake Banner
  Serial.println("NEUROSIM_HELLO,v1");
}

void loop() {
  unsigned long currentMicros = micros();

  if (currentMicros - lastSampleTime >= SAMPLE_INTERVAL_US) {
    lastSampleTime = currentMicros;
    timeSeconds += 0.004; // 1 / 250 sec
    sequenceNumber++;

    // Read potentiometer positions (0.0 to 1.0)
    float amp_delta = (float)analogRead(PIN_POT_DELTA) / 4095.0;
    float amp_theta = (float)analogRead(PIN_POT_THETA) / 4095.0;
    float amp_alpha = (float)analogRead(PIN_POT_ALPHA) / 4095.0;
    float amp_beta  = (float)analogRead(PIN_POT_BETA)  / 4095.0;

    // Microvolt scale factor
    float scale = 40.0;

    // Calculate synthetic EEG waveform
    float s_delta = amp_delta * scale * sin(2.0 * PI * FREQ_DELTA * timeSeconds);
    float s_theta = amp_theta * scale * sin(2.0 * PI * FREQ_THETA * timeSeconds);
    float s_alpha = amp_alpha * scale * sin(2.0 * PI * FREQ_ALPHA * timeSeconds);
    float s_beta  = amp_beta  * scale * sin(2.0 * PI * FREQ_BETA  * timeSeconds);

    // Pseudorandom noise (-5 to +5 uV)
    float noise = ((float)random(-100, 100) / 100.0) * 5.0;

    float waveform = s_delta + s_theta + s_alpha + s_beta + noise;

    // Checksum = (sequenceNumber + (unsigned int)(fabs(waveform) * 100.0)) % 256
    unsigned int checksum = (sequenceNumber + (unsigned int)(fabs(waveform) * 100.0)) % 256;

    // Send sample over USB Serial with packet integrity checksum
    Serial.print("SAMPLE,");
    Serial.print(waveform, 3);
    Serial.print(",");
    Serial.print(sequenceNumber);
    Serial.print(",");
    Serial.println(checksum);
  }
}
