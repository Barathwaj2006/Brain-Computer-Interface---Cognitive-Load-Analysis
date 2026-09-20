/*
 * ==============================================================================
 * NEUROSIM — ESP32 3-ELECTRODE + 1-SENSOR WI-FI TELEMETRY TRANSMITTER
 * ==============================================================================
 *
 * Dedicated clinical firmware for 3-Electrode Bio-potential Acquisition
 * + 1 Auxiliary Sensor (PPG / Galvanic Skin Response / Piezo / Analog Transducer).
 *
 * Hardware Pinout (ESP32 DevKit V1):
 * - ELECTRODE 1 (ACTIVE / FOREHEAD):   GPIO 34 (ADC1_CH6) -> Inverting / Scalp lead
 * - ELECTRODE 2 (REFERENCE / EAR):     GPIO 35 (ADC1_CH7) -> Non-inverting / Mastoid lead
 * - ELECTRODE 3 (GROUND / DRL):        GPIO 32 (ADC1_CH4) -> Driven Right Leg / GND
 * - SENSOR 1 (AUXILIARY TRANSDUCER):   GPIO 33 (ADC1_CH5) -> Pulse / GSR / Force
 *
 * Telemetry Specifications:
 * - Sampling Frequency: 250 Hz (4000 µs timer loop)
 * - Network Protocol: Wi-Fi UDP (Direct Datagrams to Laptop)
 * - Target Port: 5005
 * - Packet Format: SAMPLE,e1,e2,e3,sensor,sequence
 * - Differential EEG Calculation: V_EEG = E1 - E2 (Centered around 0 μV)
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiUdp.h>

// -----------------------------------------------------------------------------
// 1. Wi-Fi Configuration
// -----------------------------------------------------------------------------
// Current Laptop Wi-Fi SSID detected by NeuroSim: "Netvennuma"
const char* WIFI_SSID     = "Netvennuma";          // Replace if using another network
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";  // Replace with your Wi-Fi password

// Target Laptop Wi-Fi IP and Port (Set to "AUTO" for Zero-Config Discovery, or specify IP)
String      targetLaptopIp = "192.168.29.155";      // Host laptop IP (Auto-discovered or fallback)
const char* FALLBACK_IP    = "192.168.29.155";
const int   LAPTOP_PORT    = 5005;                  // NeuroSim UDP Telemetry Port

WiFiUDP udp;

// -----------------------------------------------------------------------------
// 2. Hardware Pin Allocations & Multi-Sample Batching
// -----------------------------------------------------------------------------
const int PIN_ELECTRODE_1_ACTIVE = 34; // E1 (Scalp / Forehead)
const int PIN_ELECTRODE_2_REF    = 35; // E2 (Earlobe / Mastoid Reference)
const int PIN_ELECTRODE_3_GND    = 32; // E3 (DRL / Ground reference)
const int PIN_SENSOR_AUX         = 33; // Aux 1 (PPG / Pulse / GSR / Motion)

// Multi-Sample Batching (5 samples = 20ms window @ 250 Hz; reduces Wi-Fi congestion by 80%)
#define BATCH_SIZE 5
char batchPayloadBuffer[512];
int currentBatchCount = 0;

// ADC Calibration & Microvolt Scaling
const float ADC_CENTER = 2048.0;
const float UV_PER_COUNT = 8.05; // 1 ADC count ≈ 8.05 μV

// Sampling Loop (250 Hz = 4000 microseconds)
const unsigned long SAMPLE_INTERVAL_US = 4000;
unsigned long lastSampleMicros = 0;
unsigned long sequenceCounter = 0;
bool isDiscovered = false;

void discoverLaptopHost() {
  Serial.println("[Discovery] Broadcasting discovery probe on 255.255.255.255:5005...");
  IPAddress broadcastIp(255, 255, 255, 255);
  udp.beginPacket(broadcastIp, LAPTOP_PORT);
  udp.print("DISCOVER\n");
  udp.endPacket();

  unsigned long startWait = millis();
  while (millis() - startWait < 2500) {
    int packetSize = udp.parsePacket();
    if (packetSize) {
      char reply[128];
      int len = udp.read(reply, sizeof(reply) - 1);
      if (len > 0) reply[len] = '\0';
      String msg = String(reply);
      msg.trim();
      if (msg.startsWith("DISCOVER_ACK") || msg.startsWith("NEUROSIM_BEACON")) {
        int firstComma = msg.indexOf(',');
        int secondComma = msg.indexOf(',', firstComma + 1);
        if (firstComma > 0) {
          String host = (secondComma > 0) ? msg.substring(firstComma + 1, secondComma) : msg.substring(firstComma + 1);
          host.trim();
          if (host.length() > 6) {
            targetLaptopIp = host;
            isDiscovered = true;
            Serial.print("[Discovery] Auto-discovered NeuroSim Workstation at: ");
            Serial.println(targetLaptopIp);
            return;
          }
        }
      }
    }
    delay(20);
  }
  Serial.print("[Discovery] Beacon timeout. Falling back to configured IP: ");
  Serial.println(targetLaptopIp);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n=======================================================");
  Serial.println("  NEUROSIM 3-ELECTRODE + 1-SENSOR TELEMETRY TRANSMITTER ");
  Serial.println("=======================================================");

  // Configure Analog Pins
  pinMode(PIN_ELECTRODE_1_ACTIVE, INPUT);
  pinMode(PIN_ELECTRODE_2_REF, INPUT);
  pinMode(PIN_ELECTRODE_3_GND, INPUT);
  pinMode(PIN_SENSOR_AUX, INPUT);
  analogReadResolution(12); // 12-bit resolution (0 - 4095)

  // Connect to Laptop Wi-Fi Network
  Serial.print("[Wi-Fi] Connecting to network: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 25) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[Wi-Fi] Connected successfully!");
    Serial.print("[Wi-Fi] ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    udp.begin(5005);
    discoverLaptopHost();
    Serial.print("[Wi-Fi] Target Telemetry Destination: ");
    Serial.print(targetLaptopIp);
    Serial.print(":");
    Serial.println(LAPTOP_PORT);
  } else {
    Serial.println("\n[Wi-Fi] WARNING: Could not connect to Wi-Fi. Check SSID/Password.");
    Serial.println("[USB] Continuing in high-speed USB WebSerial Mode (115200 baud).");
    udp.begin(5005);
  }

  batchPayloadBuffer[0] = '\0';
  lastSampleMicros = micros();
}

void loop() {
  unsigned long currentMicros = micros();

  // Precise 250 Hz timing clock (every 4000 µs)
  if (currentMicros - lastSampleMicros >= SAMPLE_INTERVAL_US) {
    lastSampleMicros += SAMPLE_INTERVAL_US;
    sequenceCounter++;

    // 1. Read Raw 12-bit Analog Counts
    int rawE1 = analogRead(PIN_ELECTRODE_1_ACTIVE);
    int rawE2 = analogRead(PIN_ELECTRODE_2_REF);
    int rawE3 = analogRead(PIN_ELECTRODE_3_GND);
    int rawSensor = analogRead(PIN_SENSOR_AUX);

    // 2. Convert to Microvolts (μV) centered around baseline
    float uvE1 = (rawE1 - ADC_CENTER) * UV_PER_COUNT;
    float uvE2 = (rawE2 - ADC_CENTER) * UV_PER_COUNT;
    float uvE3 = (rawE3 - ADC_CENTER) * UV_PER_COUNT;
    float valSensor = (float)rawSensor;

    // 3. Format Single Sample Line: SAMPLE,e1,e2,e3,sensor,sequence
    char singleSample[96];
    snprintf(singleSample, sizeof(singleSample),
             "SAMPLE,%.2f,%.2f,%.2f,%.1f,%lu\n",
             uvE1, uvE2, uvE3, valSensor, sequenceCounter);

    // Continuous USB WebSerial Output (Enables zero-latency browser USB streaming)
    Serial.print(singleSample);

    // 4. Multi-Sample Batched UDP Transmission
    strncat(batchPayloadBuffer, singleSample, sizeof(batchPayloadBuffer) - strlen(batchPayloadBuffer) - 1);
    currentBatchCount++;

    if (currentBatchCount >= BATCH_SIZE) {
      if (WiFi.status() == WL_CONNECTED) {
        udp.beginPacket(targetLaptopIp.c_str(), LAPTOP_PORT);
        udp.write((const uint8_t*)batchPayloadBuffer, strlen(batchPayloadBuffer));
        udp.endPacket();
      }
      batchPayloadBuffer[0] = '\0';
      currentBatchCount = 0;
    }
  }
}
