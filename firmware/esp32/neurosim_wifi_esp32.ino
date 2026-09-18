/*
 * ==============================================================================
 * NEUROSIM — ESP32 DevKit V1 Direct Laptop Wi-Fi Telemetry Transmitter
 * ==============================================================================
 *
 * Transmits real-time synthetic/potentiometer EEG waveforms directly to your
 * laptop's Wi-Fi network over high-speed UDP (Port 5005).
 *
 * Hardware Connections (DevKit V1):
 * - Delta Potentiometer (2 Hz) -> GPIO 34 (ADC1_CH6)
 * - Theta Potentiometer (6 Hz) -> GPIO 35 (ADC1_CH7)
 * - Alpha Potentiometer (10 Hz) -> GPIO 32 (ADC1_CH4)
 * - Beta Potentiometer  (20 Hz) -> GPIO 33 (ADC1_CH5)
 *
 * Telemetry Specifications:
 * - Sampling Frequency: 250 Hz (4000 µs interval loop)
 * - Transmission: Direct Wi-Fi UDP Datagrams
 * - Target Laptop Port: 5005 (UDP)
 * - Frame Format: SAMPLE,<microvolts>,<sequence_number>,<checksum>
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiUdp.h>

// -----------------------------------------------------------------------------
// 1. Wi-Fi Configuration
// Connect to the same Wi-Fi router as your laptop, or your laptop's Mobile Hotspot
// -----------------------------------------------------------------------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";      // Replace with your Laptop Hotspot / Wi-Fi SSID
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";  // Replace with your Wi-Fi Password

// Laptop Wi-Fi Target IP & Port (Displayed on NeuroSim Web Dashboard)
const char* LAPTOP_IP     = "192.168.29.155";      // Replace with your Laptop's Wi-Fi IP
const int   LAPTOP_PORT   = 5005;

WiFiUDP udp;

// -----------------------------------------------------------------------------
// 2. Hardware ADC Pin Definitions
// -----------------------------------------------------------------------------
const int PIN_POT_DELTA = 34;
const int PIN_POT_THETA = 35;
const int PIN_POT_ALPHA = 32;
const int PIN_POT_BETA  = 33;

// Clinical Target Frequencies (Hz)
const float FREQ_DELTA = 2.0;
const float FREQ_THETA = 6.0;
const float FREQ_ALPHA = 10.0;
const float FREQ_BETA  = 20.0;

// Sampling Interval (250 Hz = 4,000 microseconds)
const unsigned long SAMPLE_INTERVAL_US = 4000;
unsigned long lastSampleTime = 0;
float timeSeconds = 0.0;
unsigned long sequenceNumber = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n[NeuroSim] Initializing ESP32 Wi-Fi Neural Telemetry Node...");

  pinMode(PIN_POT_DELTA, INPUT);
  pinMode(PIN_POT_THETA, INPUT);
  pinMode(PIN_POT_ALPHA, INPUT);
  pinMode(PIN_POT_BETA, INPUT);
  analogReadResolution(12); // 0 - 4095

  // Connect to Wi-Fi
  Serial.printf("[NeuroSim] Connecting to Wi-Fi SSID: %s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[NeuroSim] Wi-Fi Connected!");
    Serial.printf("[NeuroSim] ESP32 IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[NeuroSim] Streaming UDP to Laptop Wi-Fi: %s:%d\n", LAPTOP_IP, LAPTOP_PORT);
  } else {
    Serial.println("\n[NeuroSim WARNING] Wi-Fi Connection failed. Verify SSID/Password.");
  }

  udp.begin(5006); // Local UDP listening port
}

void loop() {
  unsigned long currentMicros = micros();

  // 250 Hz precision loop
  if (currentMicros - lastSampleTime >= SAMPLE_INTERVAL_US) {
    lastSampleTime = currentMicros;
    timeSeconds += 0.004; // 1 / 250s
    sequenceNumber++;

    // Read Potentiometers (0.0 to 1.0)
    float amp_delta = (float)analogRead(PIN_POT_DELTA) / 4095.0;
    float amp_theta = (float)analogRead(PIN_POT_THETA) / 4095.0;
    float amp_alpha = (float)analogRead(PIN_POT_ALPHA) / 4095.0;
    float amp_beta  = (float)analogRead(PIN_POT_BETA)  / 4095.0;

    // Amplitude scale in microvolts (uV)
    float scale = 40.0;

    // Synthesize composite EEG waveform
    float s_delta = amp_delta * scale * sin(2.0 * PI * FREQ_DELTA * timeSeconds);
    float s_theta = amp_theta * scale * sin(2.0 * PI * FREQ_THETA * timeSeconds);
    float s_alpha = amp_alpha * scale * sin(2.0 * PI * FREQ_ALPHA * timeSeconds);
    float s_beta  = amp_beta  * scale * sin(2.0 * PI * FREQ_BETA  * timeSeconds);

    // Pseudorandom noise (-5 to +5 uV)
    float noise = ((float)random(-100, 100) / 100.0) * 5.0;
    float waveform = s_delta + s_theta + s_alpha + s_beta + noise;

    // Checksum = (sequenceNumber + (unsigned int)(fabs(waveform) * 100.0)) % 256
    unsigned int checksum = (sequenceNumber + (unsigned int)(fabs(waveform) * 100.0)) % 256;

    // Construct Telemetry Packet
    char packet[64];
    snprintf(packet, sizeof(packet), "SAMPLE,%.3f,%lu,%u", waveform, sequenceNumber, checksum);

    // Send UDP Datagram over Wi-Fi directly to Laptop
    if (WiFi.status() == WL_CONNECTED) {
      udp.beginPacket(LAPTOP_IP, LAPTOP_PORT);
      udp.write((const uint8_t*)packet, strlen(packet));
      udp.endPacket();
    }

    // Mirror to USB Serial (1 in every 25 samples for logging)
    if (sequenceNumber % 25 == 0) {
      Serial.println(packet);
    }
  }
}
