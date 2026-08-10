# Current Development Status

## Project
NeuroSim × Pokidex

## Last Agent
Antigravity

## Task Completed
Prevent automatic synthetic signal generation.

## Root Cause
In `src/ui/main_window.py`, `self.active_hardware_source` defaulted to `"SIMULATOR"` in `MainWindow.__init__()`. Additionally, `MainWindow.init_dsp_timer()` starts a 25 FPS recurring `QTimer` firing `process_dsp_frame()`. Whenever `active_hardware_source == "SIMULATOR"`, `process_dsp_frame()` called `self.generator.generate_chunk()` to append synthetic samples into `signal_buffer` every 40 ms. Consequently, waveforms, PSD metrics, and cognitive load classifications were automatically generated and displayed on startup even when no input hardware was connected.

## Changes Made
- [`src/ui/main_window.py`](file:///C:/Users/barat/.gemini/antigravity/scratch/neurosim-eeg-cognitive-analysis/src/ui/main_window.py): Changed default `active_hardware_source` to `"IDLE"`. Added early return in `process_dsp_frame()` when `signal_buffer` has fewer than 32 samples. Added `start_simulator()` method to allow explicit manual activation of simulator mode. Updated `disconnect_all_hardware()` to reset state to `"IDLE"` and clear `signal_buffer`.
- [`src/ui/screens/hardware_screen.py`](file:///C:/Users/barat/.gemini/antigravity/scratch/neurosim-eeg-cognitive-analysis/src/ui/screens/hardware_screen.py): Added `start_simulator_requested` signal and added `🎮 START DEMO SIMULATOR` action button for manual simulator selection.
- [`tests/test_idle_behavior.py`](file:///C:/Users/barat/.gemini/antigravity/scratch/neurosim-eeg-cognitive-analysis/tests/test_idle_behavior.py): Added unit tests verifying default IDLE launch state, sample prevention, manual simulator activation, and disconnect behavior.

## Behavior Before
NeuroSim defaulted to `SIMULATOR` and generated synthetic samples every 40 ms even when no input device was connected.

## Behavior After
NeuroSim starts in `IDLE` / `DISCONNECTED`.
No external input:
→ no samples
→ no waveform
→ no DSP
→ no classification.
Explicit simulator selection remains available when manually requested (`start_simulator()`).

## Tests Executed
```powershell
venv\Scripts\python.exe -m pytest
```

## Test Result
PASS — 24 passed in 7.42s.

## Manual Validation
- Launched application from source (`python src/main.py`). Verified `signal_buffer` is empty on startup and no waveform/PSD/classification is rendered.
- Tested explicit click on `🎮 START DEMO SIMULATOR` button in Hardware Center UI; verified state transitions to `● SIMULATOR ACTIVE` and synthetic waveform begins streaming.
- Tested disconnection; verified state resets to `IDLE` and `signal_buffer` is cleared.

## Current Commit
Commit Hash: `d2608c91b48b6955641f1563ec1d4d083718d9c4` (short: `d2608c9`)  
Commit Message: `fix: prevent automatic synthetic signal generation`

## Files Safe for Next Agent
- `src/acquisition/pokidex_client.py`
- `src/acquisition/device_scanner.py`
- `src/ui/screens/hardware_screen.py`
- `tests/test_pokidex_client.py`

## Files Currently Protected
- `src/processing/psd.py` (DSP algorithms & Welch FFT)
- `src/processing/filter.py` (Butterworth filter)
- `src/classification/rule_classifier.py` & `ml_classifier.py` (Classifiers)
- `src/reporting/pdf_generator.py` & `ai_engine.py` (Reporting)
- `firmware/esp32/neurosim_esp32.ino` (ESP32 firmware)

## Known Issues
None known.

## Next Recommended Task
Integrate and validate Pokidex BLE & Wi-Fi input streaming with real Android Pokidex app hardware.

## Instructions to Google AI Studio
Google AI Studio should first pull the latest master branch (`git pull origin master`) and verify commit `d2608c91b48b6955641f1563ec1d4d083718d9c4` before making changes.

Do not modify protected files (`src/processing/psd.py`, `src/processing/filter.py`, `src/classification/rule_classifier.py`, `src/classification/ml_classifier.py`, `src/reporting/pdf_generator.py`) unless required.

The next task is to validate and test live streaming from Pokidex over Wi-Fi WebSocket (`ws://<host>:8765`) and BLE GATT (`0000fe50-0000-1000-8000-00805f9b34fb`).
