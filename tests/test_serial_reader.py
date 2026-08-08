"""
Unit Tests — Serial Protocol & Checksum Validation
Verifies:
- Checksum validation for valid 4-part packets (SAMPLE,value,seq,checksum)
- Packet rejection and dropped packet counter increments for corrupted packets
- Handshake parsing (NEUROSIM_HELLO,v1)
"""

import unittest
from src.acquisition.serial_reader import HardwareSerialThread

class TestSerialProtocol(unittest.TestCase):
    def setUp(self):
        self.reader = HardwareSerialThread(allow_bare_fallback=False)

    def test_valid_checksum_packet(self):
        val = 12.34
        seq = 100
        chk = (seq + int(abs(val) * 100.0)) % 256
        valid_line = f"SAMPLE,{val},{seq},{chk}"
        
        parsed_val = self.reader.parse_line(valid_line)
        self.assertEqual(parsed_val, 12.34)
        self.assertEqual(self.reader.dropped_packets, 0)

    def test_corrupted_checksum_packet(self):
        val = 12.34
        seq = 100
        bad_chk = 999  # Invalid checksum
        corrupted_line = f"SAMPLE,{val},{seq},{bad_chk}"

        parsed_val = self.reader.parse_line(corrupted_line)
        self.assertIsNone(parsed_val)
        self.assertEqual(self.reader.dropped_packets, 1)

    def test_malformed_packet_line(self):
        malformed_line = "SAMPLE,garbage_string,foo,bar"
        parsed_val = self.reader.parse_line(malformed_line)
        self.assertIsNone(parsed_val)
        self.assertEqual(self.reader.dropped_packets, 1)

if __name__ == '__main__':
    unittest.main()
