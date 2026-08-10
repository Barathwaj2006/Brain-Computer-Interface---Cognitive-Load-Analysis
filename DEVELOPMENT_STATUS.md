# Current Development Status

## Phase & Agent
PHASE=1A
AGENT=ANTIGRAVITY
REPOSITORY=NEUROSIM
BRANCH=rebuild/neurosim-v2
TASK=canonical signal contract
COMMIT=c8669427ce7aee70c1e84aa6bd66d15655bd5be2
TESTS=34/34 PASS
POKIDEX=FROZEN
WORKTREE=CLEAN

## Canonical Signal Contract Specification
- **Contract Location**: [`src/core/signal_contract.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/core/signal_contract.py)
- **Source Enum Location**: [`src/core/enums.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/core/enums.py)
- **Fields**:
  - `timestamp`: `float` (positive epoch timestamp)
  - `sequence`: `int` (non-negative monotonically increasing integer)
  - `sampling_rate`: `int` (positive integer Hz)
  - `channel_count`: `int` (positive integer channel count)
  - `channels`: `Tuple[str, ...]` (tuple of channel label strings matching `channel_count`)
  - `data`: `Tuple[Tuple[float, ...], ...]` (2D tuple of float sample values `(channel_count, num_samples)`)
  - `source`: `SignalSourceType` (`SIMULATOR`, `ESP32_USB`, `ESP32_WIFI`, `EEG_HARDWARE`, `UNKNOWN`)
  - `metadata`: `MappingProxyType[str, Any]` (frozen immutable dictionary)
- **Validation Rules**:
  - `sampling_rate` > 0
  - `channel_count` > 0
  - `sequence` >= 0
  - `timestamp` > 0
  - `channels` length matches `channel_count`
  - `data` channel length matches `channel_count`
  - All sample values must be finite numbers (rejects NaN, Inf, non-numeric strings, and booleans)
  - All channels must contain equal sample lengths
- **Serialization Behavior**:
  - `to_dict()` / `from_dict()` for dictionary mapping
  - `to_json()` / `from_json()` for deterministic JSON string representations
- **Files Owned by Task**:
  - `src/core/__init__.py`
  - `src/core/enums.py`
  - `src/core/signal_contract.py`
  - `tests/test_signal_contract.py`

## Integration Notes for Next Agent (Google AI Studio)
1. Build quantitative analysis foundation against this canonical signal contract ([`src/core/signal_contract.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/core/signal_contract.py)).
2. Do not modify `src/core/` files unless a blocking defect is discovered.
3. Keep Pokidex completely frozen.
