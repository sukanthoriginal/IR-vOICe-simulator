import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server

ROOT = Path(__file__).resolve().parents[1]


class ServerPersistenceTests(unittest.TestCase):
    def test_result_is_written_identically_to_primary_and_mirror(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            primary = root / "primary"
            mirror = root / "mirror"
            csv_text = "participant_id,correct\nP-001,1\n"

            with patch.object(
                server,
                "TEST_DATA_DIRS",
                (str(primary), str(mirror)),
            ):
                destinations = server.save_result_copies("pilot.csv", csv_text)

            self.assertEqual(
                destinations,
                [str(primary / "pilot.csv"), str(mirror / "pilot.csv")],
            )
            self.assertEqual((primary / "pilot.csv").read_text(), csv_text)
            self.assertEqual((mirror / "pilot.csv").read_text(), csv_text)

    def test_native_launcher_configures_both_result_directories(self):
        launcher = (
            ROOT
            / "tools"
            / "l2_native_app_template"
            / "vOICe-L2-Native-Launcher"
        ).read_text()
        self.assertIn("IR_VOICE_TEST_DATA_DIR", launcher)
        self.assertIn("IR_VOICE_TEST_DATA_MIRROR_DIR", launcher)
        self.assertIn("Application Support/vOICe L2 Native Aspect", launcher)
        self.assertIn("Dev/Lossfunk/ir-results/l2-native-aspect", launcher)


if __name__ == "__main__":
    unittest.main()
