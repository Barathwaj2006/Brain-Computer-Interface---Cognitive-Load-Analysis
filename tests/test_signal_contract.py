"""
Phase 1A Canonical Signal Contract Unit Tests for NeuroSim 2.0
Validates single-channel/multi-channel frames, validation error handling, immutability,
metadata freezing, and JSON/dict serialization.
"""

import unittest
import json
import time
import numpy as np
from dataclasses import FrozenInstanceError
from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame

class TestSignalContract(unittest.TestCase):

    def test_01_valid_single_channel_frame(self):
        """1. Valid single-channel frame creation."""
        t_now = time.time()
        frame = SignalFrame(
            timestamp=t_now,
            sequence=100,
            sampling_rate=250,
            channel_count=1,
            channels=("Ch1",),
            data=([12.5, 14.8, -3.2, 0.0],),
            source=SignalSourceType.SIMULATOR,
            metadata={"gain": 24}
        )
        self.assertEqual(frame.timestamp, t_now)
        self.assertEqual(frame.sequence, 100)
        self.assertEqual(frame.sampling_rate, 250)
        self.assertEqual(frame.channel_count, 1)
        self.assertEqual(frame.channels, ("Ch1",))
        self.assertEqual(frame.num_samples, 4)
        self.assertEqual(frame.get_channel_data(0), (12.5, 14.8, -3.2, 0.0))
        self.assertEqual(frame.source, SignalSourceType.SIMULATOR)
        self.assertEqual(frame.metadata["gain"], 24)

    def test_02_valid_multi_channel_frame(self):
        """2. Valid multi-channel frame creation."""
        t_now = time.time()
        frame = SignalFrame(
            timestamp=t_now,
            sequence=200,
            sampling_rate=500,
            channel_count=4,
            channels=("F3", "F4", "C3", "C4"),
            data=(
                (1.0, 2.0, 3.0),
                (4.0, 5.0, 6.0),
                (7.0, 8.0, 9.0),
                (10.0, 11.0, 12.0)
            ),
            source=SignalSourceType.EEG_HARDWARE
        )
        self.assertEqual(frame.channel_count, 4)
        self.assertEqual(frame.channels, ("F3", "F4", "C3", "C4"))
        self.assertEqual(frame.num_samples, 3)
        self.assertEqual(frame.get_channel_data(2), (7.0, 8.0, 9.0))
        self.assertEqual(frame.source, SignalSourceType.EEG_HARDWARE)

    def test_03_invalid_sampling_rate(self):
        """3. Invalid sampling rate handling."""
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=0, channel_count=1, channels=("Ch1",), data=([1.0],))

        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=-250, channel_count=1, channels=("Ch1",), data=([1.0],))

    def test_04_invalid_channel_count(self):
        """4. Invalid channel count handling."""
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=0, channels=(), data=())

        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=-1, channels=(), data=())

    def test_05_channel_data_mismatch(self):
        """5. Channel/data count or length mismatch handling."""
        # Channels list count (2) does not match channel_count (1)
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1", "Ch2"), data=([1.0],))

        # Data rows (2) does not match channel_count (1)
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([1.0], [2.0]))

        # Channel sample lengths differ (3 vs 2)
        with self.assertRaises(ValueError):
            SignalFrame(
                timestamp=1.0, sequence=0, sampling_rate=250, channel_count=2, channels=("Ch1", "Ch2"),
                data=((1.0, 2.0, 3.0), (4.0, 5.0))
            )

    def test_06_invalid_sample_values(self):
        """6. Invalid sample value rejection (NaN, Inf, strings, bools)."""
        # NaN value
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([float('nan')],))

        # Inf value
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([float('inf')],))

        # String value
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=(["not_a_number"],))

        # Boolean value
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([True],))

    def test_07_metadata_handling(self):
        """7. Metadata freezing and immutability."""
        meta = {"device": "ESP32", "gain": 24}
        frame = SignalFrame(
            timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([1.0],),
            metadata=meta
        )
        # Verify metadata is frozen mapping or protected copy
        with self.assertRaises(TypeError):
            frame.metadata["device"] = "Hacked"

        # Verify modifying original dict does not mutate frame metadata
        meta["device"] = "Modified"
        self.assertEqual(frame.metadata["device"], "ESP32")

    def test_08_deterministic_serialization(self):
        """8. Deterministic dict and JSON serialization / deserialization."""
        t_now = 1700000000.0
        frame = SignalFrame(
            timestamp=t_now, sequence=42, sampling_rate=250, channel_count=2,
            channels=("Ch1", "Ch2"), data=((10.5, 20.5), (30.5, 40.5)),
            source=SignalSourceType.ESP32_USB, metadata={"test_id": 123}
        )

        d = frame.to_dict()
        self.assertEqual(d["timestamp"], t_now)
        self.assertEqual(d["sequence"], 42)
        self.assertEqual(d["source"], "ESP32_USB")

        reconstructed_from_dict = SignalFrame.from_dict(d)
        self.assertEqual(reconstructed_from_dict, frame)

        json_str = frame.to_json()
        reconstructed_from_json = SignalFrame.from_json(json_str)
        self.assertEqual(reconstructed_from_json, frame)

    def test_09_immutability_and_mutation_protection(self):
        """9. Immutability and mutation protection."""
        frame = SignalFrame(
            timestamp=1.0, sequence=10, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([1.0, 2.0],)
        )
        with self.assertRaises((FrozenInstanceError, TypeError, AttributeError)):
            frame.sequence = 999

        with self.assertRaises((FrozenInstanceError, TypeError, AttributeError)):
            frame.data = ([5.0, 6.0],)

    def test_10_sequence_timestamp_validation(self):
        """10. Sequence and timestamp validation."""
        # Negative sequence
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=1.0, sequence=-1, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([1.0],))

        # Negative timestamp
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=-10.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([1.0],))

        # Zero timestamp
        with self.assertRaises(ValueError):
            SignalFrame(timestamp=0.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([1.0],))

if __name__ == "__main__":
    unittest.main()
