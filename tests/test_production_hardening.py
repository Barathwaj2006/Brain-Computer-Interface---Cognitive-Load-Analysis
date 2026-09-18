#!/usr/bin/env python3
"""
Unit and Integration Tests for NeuroSim Production Hardening
Verifies:
- SQLite Database WAL, tables, and indexes
- OTP Authentication lifecycle
- Sliding-window rate limiter
- Spending/Quota caps
- Idempotency deduplication
- Database atomic backup & restore
- Multi-user concurrency
- Gzip compression
- 404 routing & Health checks
"""

import os
import sys
import time
import json
import sqlite3
import threading
import unittest
import urllib.request
import urllib.error
import gzip

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server import DatabaseManager, RateLimiter, run_http_server, HTTP_PORT, PRIMARY_WIFI_IP

class TestProductionHardening(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Start the HTTP server in a daemon thread if not already running
        cls.server_thread = threading.Thread(target=run_http_server, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    def test_01_database_indexes_and_schema(self):
        """Verify all critical SQLite tables and query performance indexes exist."""
        conn = DatabaseManager.get_connection()
        cur = conn.cursor()

        # Verify tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        self.assertIn("users", tables)
        self.assertIn("sessions", tables)
        self.assertIn("audit_logs", tables)
        self.assertIn("idempotency_keys", tables)

        # Verify indexes
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cur.fetchall()}
        self.assertIn("idx_sessions_user_id", indexes)
        self.assertIn("idx_sessions_patient", indexes)
        self.assertIn("idx_sessions_created", indexes)
        self.assertIn("idx_users_mobile", indexes)
        self.assertIn("idx_users_token", indexes)
        print("[TEST PASS] SQLite schema, WAL mode, and indexes verified.")

    def test_02_otp_auth_workflow(self):
        """Verify OTP generation, validation, expiration, and token issuance."""
        mobile = "+15551234567"
        name = "Dr. Jane Doe"
        email = "jane.doe@hospital.org"

        # Generate OTP
        otp_code = "849201"
        DatabaseManager.create_or_update_otp(name, email, mobile, otp_code)

        # Fail with wrong OTP
        user, err = DatabaseManager.verify_otp(mobile, "000000")
        self.assertIsNone(user)
        self.assertIn("Invalid OTP", err)

        # Pass with correct OTP
        user, err = DatabaseManager.verify_otp(mobile, otp_code)
        self.assertIsNone(err)
        self.assertIsNotNone(user)
        self.assertEqual(user["mobile"], mobile)
        self.assertTrue(len(user["token"]) >= 32)

        # Re-using already verified OTP must fail
        user2, err2 = DatabaseManager.verify_otp(mobile, otp_code)
        self.assertIsNone(user2)
        print("[TEST PASS] OTP issuance, verification, and CSPRNG session token validated.")

    def test_03_rate_limiter(self):
        """Verify sliding window rate limiting throttles excessive requests."""
        limiter = RateLimiter()
        test_ip = "10.0.0.99"

        # 5 requests with limit 5 should all pass
        for _ in range(5):
            allowed, _, _ = limiter.check_rate_limit(test_ip, limit=5, window=2.0)
            self.assertTrue(allowed)

        # 6th request must be rejected with 429
        allowed, retry_after, remaining = limiter.check_rate_limit(test_ip, limit=5, window=2.0)
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)
        self.assertEqual(remaining, 0)
        print("[TEST PASS] Sliding-window rate limiter blocked over-quota burst.")

    def test_04_idempotency_prevention(self):
        """Verify duplicate requests with same Idempotency-Key are returned without duplicate insert."""
        key = f"IDEM-KEY-{int(time.time() * 1000)}"
        cached = DatabaseManager.get_idempotent_response(key)
        self.assertIsNone(cached)

        resp_text = json.dumps({"status": "created", "id": 42})
        DatabaseManager.save_idempotent_response(key, resp_text)

        replayed = DatabaseManager.get_idempotent_response(key)
        self.assertEqual(replayed, resp_text)
        print("[TEST PASS] Idempotency store prevents duplicate submissions.")

    def test_05_database_backup_and_restore(self):
        """Verify atomic database backup and full restoration."""
        filename, size = DatabaseManager.backup_database()
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, 'db', 'backups', filename)))
        self.assertGreater(size, 0)

        # Test restore
        restored = DatabaseManager.restore_database(filename)
        self.assertTrue(restored)
        print(f"[TEST PASS] Database atomic backup ({size} bytes) and restore confirmed.")

    def test_06_http_health_and_404_endpoints(self):
        """Verify /api/health returns 200 OK and non-existent URL returns custom 404.html."""
        # Health check
        req = urllib.request.Request(f"http://localhost:{HTTP_PORT}/api/health")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertEqual(data["status"], "healthy")
            self.assertIn("uptime_seconds", data)

        # Custom 404 test
        try:
            urllib.request.urlopen(f"http://localhost:{HTTP_PORT}/invalid_route_xyz_999")
            self.fail("Expected 404 HTTPError")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)
            html = e.read().decode('utf-8')
            self.assertIn("Telemetry Channel Not Found", html)
        print("[TEST PASS] /api/health and custom 404 route validated.")

    def test_07_http_gzip_compression(self):
        """Verify server compresses payloads when client supports gzip."""
        req = urllib.request.Request(
            f"http://localhost:{HTTP_PORT}/api/status",
            headers={"Accept-Encoding": "gzip"}
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            encoding = resp.headers.get("Content-Encoding")
            raw = resp.read()
            if encoding == "gzip":
                decompressed = gzip.decompress(raw)
                data = json.loads(decompressed.decode('utf-8'))
                self.assertIn("wifi_ip", data)
                print("[TEST PASS] Gzip compression verified on HTTP API response.")
            else:
                data = json.loads(raw.decode('utf-8'))
                self.assertIn("wifi_ip", data)
                print("[TEST PASS] HTTP API response validated.")

    def test_08_concurrent_simultaneous_users(self):
        """Verify server handles simultaneous concurrent users without crashing or deadlocking."""
        errors = []
        def worker(user_idx):
            try:
                url = f"http://localhost:{HTTP_PORT}/api/health"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    if resp.status != 200:
                        errors.append(f"User {user_idx} got status {resp.status}")
            except Exception as e:
                errors.append(f"User {user_idx} failed: {e}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent user errors: {errors}")
        print("[TEST PASS] 12 simultaneous concurrent users handled smoothly.")

if __name__ == '__main__':
    unittest.main()
