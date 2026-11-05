import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

source = Path(__file__).with_name("garmin_probe.py")
if not source.exists():
    source = Path(__file__).resolve().parents[2] / "src" / "tools" / "garmin_probe.py"
spec = importlib.util.spec_from_file_location("garmin_probe", source)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class GarminProbeTests(unittest.TestCase):
    def test_plain_text_token(self):
        session = Mock()
        response = Mock(status_code=200, headers={"Content-Type": "text/plain"}, text="test.token.value")
        response.json.side_effect = ValueError
        session.request.return_value = response
        client = probe.GarminClient("test-key", session)
        client.authenticate()
        self.assertEqual(client.token, "test.token.value")

    def test_key_is_used_only_for_token_exchange(self):
        session = Mock()
        token = Mock(status_code=200)
        token.json.return_value = {"access_token": "test-token"}
        data = Mock(status_code=200)
        data.json.return_value = {"steps": 12}
        session.request.side_effect = [token, data]
        client = probe.GarminClient("test-key", session)
        self.assertEqual(client.get("/test"), {"steps": 12})
        calls = session.request.call_args_list
        self.assertEqual(calls[0].kwargs["headers"]["Authorization"], "ApiKey test-key")
        self.assertEqual(calls[1].kwargs["headers"]["Authorization"], "Bearer test-token")
        self.assertFalse(calls[1].kwargs["allow_redirects"])

    def test_errors_do_not_include_response_body(self):
        session = Mock()
        session.request.return_value = Mock(status_code=401, text="secret-body")
        with self.assertRaisesRegex(probe.GarminError, "HTTP 401") as caught:
            probe.GarminClient("test-key", session).authenticate()
        self.assertNotIn("secret", str(caught.exception))

    def test_no_data_and_inventory(self):
        session = Mock()
        session.request.return_value = Mock(status_code=204)
        client = probe.GarminClient("test-key", session)
        client.token = "test-token"
        self.assertIsNone(client.get("/test"))
        fields = probe.field_inventory({"sleep": [{"score": 90}, {"score": None}]})
        self.assertEqual(fields["sleep[].score"], {"int", "NoneType"})
        self.assertNotIn("90", str(fields))

    def test_collection_preserves_partial_results_and_private_files(self):
        from datetime import date
        client = Mock()
        client.get.side_effect = [{"steps": 12}, probe.GarminError("Garmin returned HTTP 403."), None, {}, [], []]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            report = probe.collect(client, date(2026, 11, 4), date(2026, 11, 4), output)
            self.assertEqual(len(report["samples"]), 6)
            self.assertEqual(report["samples"][1]["status"], "error")
            self.assertEqual(report["samples"][2]["status"], "no_data")
            self.assertEqual((output / "inventory.json").stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
