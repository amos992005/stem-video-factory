import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from circuit_assets import create_circuit, energy_latex
from edge_tts_service import EdgeTTSService


class PipelineTests(unittest.TestCase):
    def test_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            svg = create_circuit(Path(tmp) / "rc.svg").read_text()
        self.assertIn("<svg", svg)
        self.assertIn("white", svg.lower())
        self.assertEqual(energy_latex(), r"E = \frac{C V^{2}}{2}")

    def test_audio_generation_and_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = EdgeTTSService(cache_dir=tmp)
            def save_audio(path):
                Path(path).write_bytes(b"mock audio")
            with patch("edge_tts.Communicate") as communicate:
                communicate.return_value.save_sync.side_effect = save_audio
                result = service.generate_from_text("Hello world")
                self.assertEqual((Path(tmp) / result["original_audio"]).read_bytes(), b"mock audio")
                communicate.assert_called_once_with("Hello world", "en-US-ChristopherNeural", rate="+0%")
                (Path(tmp) / "cache.json").write_text(json.dumps([result]))
                service.generate_from_text("Hello world")
                self.assertEqual(communicate.call_count, 1)
                EdgeTTSService(voice="en-US-JennyNeural", cache_dir=tmp).generate_from_text("Hello world")
                self.assertEqual(communicate.call_count, 2)

    def test_failed_request_leaves_no_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = EdgeTTSService(cache_dir=tmp)
            with patch("edge_tts.Communicate") as communicate:
                communicate.return_value.save_sync.side_effect = RuntimeError("offline")
                with self.assertRaisesRegex(RuntimeError, "offline"):
                    service.generate_from_text("Hello")
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
