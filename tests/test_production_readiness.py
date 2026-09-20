import unittest
import json
import urllib.request
import urllib.error
import threading
import time
import os
import re
from http.server import ThreadingHTTPServer
from server import NeuroSimHTTPHandler, DatabaseManager, rate_limiter

class TestProductionReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start a test server on ephemeral port
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 0), NeuroSimHTTPHandler)
        cls.port = cls.httpd.server_port
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        # Give server time to bind and listen
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_backend_honeypot_bot_rejection(self):
        """Verify automated bots submitting honeypot field are rejected with HTTP 400."""
        url = f"{self.base_url}/api/auth/login"
        payload = json.dumps({
            "name": "Spam Bot 3000",
            "email": "bot@spamnet.ru",
            "role": "Bot",
            "hp_clinical_token": "malicious_bot_token_value"
        }).encode('utf-8')

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)
        body = json.loads(ctx.exception.read().decode('utf-8'))
        self.assertFalse(body.get("success", True))
        self.assertIn("bot", body.get("error", "").lower())

    def test_backend_email_and_name_validation(self):
        """Verify server validates institutional email format and name length."""
        url = f"{self.base_url}/api/auth/login"
        
        # Test 1: Invalid email format
        bad_email_payload = json.dumps({
            "name": "Dr. Valid Name",
            "email": "not-an-email",
            "role": "Neurologist"
        }).encode('utf-8')
        req = urllib.request.Request(url, data=bad_email_payload, headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

        # Test 2: Name too short
        bad_name_payload = json.dumps({
            "name": "X",
            "email": "dr.valid@hospital.org",
            "role": "Neurologist"
        }).encode('utf-8')
        req = urllib.request.Request(url, data=bad_name_payload, headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

        # Test 3: Valid clinician login succeeds
        valid_payload = json.dumps({
            "name": "Dr. Sarah Connor, MD",
            "email": "sarah.connor@neurosim.org",
            "role": "Lead Clinical Neurologist"
        }).encode('utf-8')
        req = urllib.request.Request(url, data=valid_payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertTrue(data.get("success"))
            self.assertIn("token", data)
            self.assertEqual(data["user"]["name"], "Dr. Sarah Connor, MD")

    def test_cors_preflight_options(self):
        """Verify OPTIONS preflight returns standard CORS headers and caching."""
        req = urllib.request.Request(f"{self.base_url}/api/status", method='OPTIONS')
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 204)
            self.assertEqual(resp.headers.get('Access-Control-Allow-Origin'), '*')
            allowed_headers = resp.headers.get('Access-Control-Allow-Headers', '')
            self.assertIn('Content-Type', allowed_headers)
            self.assertIn('Authorization', allowed_headers)
            self.assertIn('X-Requested-With', allowed_headers)
            self.assertEqual(resp.headers.get('Access-Control-Max-Age'), '86400')

    def test_service_worker_cache_assets_exist(self):
        """Verify all declared static assets in service-worker.js exist in web directory."""
        sw_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'service-worker.js')
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'const STATIC_ASSETS = \[(.*?)\];', content, re.DOTALL)
        self.assertIsNotNone(match, "STATIC_ASSETS array found in service-worker.js")
        raw_assets = match.group(1)
        assets = [a.strip().strip("'\"") for a in raw_assets.split(',') if a.strip()]

        web_dir = os.path.join(os.path.dirname(__file__), '..', 'web')
        for asset in assets:
            if asset in ('/', ''):
                continue
            clean_path = asset.lstrip('/')
            file_path = os.path.join(web_dir, clean_path)
            self.assertTrue(os.path.exists(file_path), f"Asset {asset} must exist at {file_path}")

    def test_vercel_security_headers_configuration(self):
        """Verify vercel.json contains HSTS, CSP, and Permissions-Policy."""
        vercel_path = os.path.join(os.path.dirname(__file__), '..', 'vercel.json')
        with open(vercel_path, 'r', encoding='utf-8') as f:
            v_cfg = json.load(f)

        headers = v_cfg.get('headers', [])
        all_header_keys = [h['key'] for group in headers for h in group.get('headers', [])]
        self.assertIn('Strict-Transport-Security', all_header_keys)
        self.assertIn('Permissions-Policy', all_header_keys)
        self.assertIn('Content-Security-Policy', all_header_keys)
        self.assertIn('X-Content-Type-Options', all_header_keys)
        self.assertIn('X-Frame-Options', all_header_keys)

if __name__ == '__main__':
    unittest.main()
