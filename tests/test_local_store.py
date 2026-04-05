import os
import tempfile
import unittest

from services.local_store import delete_sqlite_payload, load_sqlite_payload, save_sqlite_payload


class LocalStoreSmokeTests(unittest.TestCase):
    def test_sqlite_round_trip_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "state.sqlite3")
            payload = {"foo": "bar", "n": 1, "_meta": {"version": 1}}

            self.assertTrue(save_sqlite_payload(db_path, payload))
            loaded = load_sqlite_payload(db_path)
            self.assertIsInstance(loaded, dict)
            self.assertEqual(loaded.get("foo"), "bar")
            self.assertEqual(loaded.get("n"), 1)

    def test_rejects_non_dict_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "state.sqlite3")
            self.assertFalse(save_sqlite_payload(db_path, [1, 2, 3]))

    def test_delete_sqlite_payload_removes_db(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "state.sqlite3")
            self.assertTrue(save_sqlite_payload(db_path, {"ok": True}))
            self.assertTrue(os.path.exists(db_path))

            delete_sqlite_payload(db_path)
            self.assertFalse(os.path.exists(db_path))


if __name__ == "__main__":
    unittest.main()
