import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "session-to-skill" / "scripts" / "session_to_skill.py"
spec = importlib.util.spec_from_file_location("session_to_skill", MODULE_PATH)
session_to_skill = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["session_to_skill"] = session_to_skill
spec.loader.exec_module(session_to_skill)


class SessionToSkillTests(unittest.TestCase):
    def test_markdown_fixture_matches_expected_report(self):
        root = Path(__file__).resolve().parents[1]
        fixture = Path("session-to-skill/fixtures/sample-session.md")
        expected = (root / "session-to-skill" / "fixtures" / "expected-report.md").read_text(encoding="utf-8")

        events = session_to_skill.extract_events([fixture])
        report = session_to_skill.render_report([fixture], events)

        self.assertEqual(report, expected)

    def test_jsonl_content_is_extracted_and_redacted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "session.jsonl"
            rows = [
                {
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Always validate with api_key=abcdef1234567890 at https://example.com/private?token=abc before emailing ops@example.com.",
                            }
                        ],
                    }
                },
                {
                    "message": {
                        "role": "assistant",
                        "content": "I ran `npm test` and wrote the report.",
                    }
                },
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

            events = session_to_skill.extract_events([path])
            text = "\n".join(event.text for event in events)

            self.assertIn("api_key=[REDACTED]", text)
            self.assertNotIn("abcdef1234567890", text)
            self.assertIn("[URL]", text)
            self.assertNotIn("https://example.com/private", text)
            self.assertIn("[EMAIL]", text)
            self.assertNotIn("ops@example.com", text)
            self.assertIn("npm test", text)

    def test_directory_scan_ignores_non_text_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.md").write_text("Create a skill from this repeated workflow.", encoding="utf-8")
            (root / "b.bin").write_bytes(b"\x00\x01\x02")

            events = session_to_skill.extract_events([root])

            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].source.name, "a.md")

    def test_report_handles_empty_corpus(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = session_to_skill.render_report([root], [])

            self.assertIn("- Files scanned: 0", report)
            self.assertIn("| No candidate | 0 |", report)


if __name__ == "__main__":
    unittest.main()
