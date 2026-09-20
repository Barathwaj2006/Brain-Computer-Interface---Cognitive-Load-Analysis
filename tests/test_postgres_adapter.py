import unittest
from server import PostgresCursorWrapper

class DummyCursor:
    def __init__(self):
        self.executed_query = None
        self.executed_params = None
        self.rowcount = 1

    def execute(self, query, params=None):
        self.executed_query = query
        self.executed_params = params

    def fetchone(self):
        return {"id": 42}

    def fetchall(self):
        return [{"id": 42}]


class TestPostgresAdapter(unittest.TestCase):
    def test_parameter_placeholder_translation(self):
        raw = DummyCursor()
        wrapper = PostgresCursorWrapper(raw)
        wrapper.execute("SELECT * FROM users WHERE email = ? AND mobile = ?", ("test@local", "1234567890"))
        self.assertEqual(raw.executed_query, "SELECT * FROM users WHERE email = %s AND mobile = %s")
        self.assertEqual(raw.executed_params, ("test@local", "1234567890"))

    def test_idempotency_conflict_translation(self):
        raw = DummyCursor()
        wrapper = PostgresCursorWrapper(raw)
        wrapper.execute(
            "INSERT OR REPLACE INTO idempotency_keys (key, response_body, created_at) VALUES (?, ?, ?)",
            ("key1", "body", 100.0)
        )
        self.assertIn("ON CONFLICT (key) DO UPDATE", raw.executed_query)

    def test_returning_id_injection(self):
        raw = DummyCursor()
        wrapper = PostgresCursorWrapper(raw)
        wrapper.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Alice", "alice@example.com"))
        self.assertTrue(raw.executed_query.strip().endswith("RETURNING id;"))
        self.assertEqual(wrapper.lastrowid, 42)


if __name__ == '__main__':
    unittest.main()
