import os
import unittest
from unittest.mock import patch

from config_floosy import _is_local_runtime_url, _is_shared_hosted_url, _local_persistence_enabled


class RuntimeDetectionTests(unittest.TestCase):
    def test_detects_streamlit_app_domain_as_shared_hosted(self):
        self.assertTrue(_is_shared_hosted_url("https://floosy-beta.streamlit.app"))

    def test_detects_share_streamlit_io_domain_as_shared_hosted(self):
        self.assertTrue(_is_shared_hosted_url("https://share.streamlit.io"))

    def test_localhost_is_not_shared_hosted(self):
        self.assertFalse(_is_shared_hosted_url("http://localhost:8501"))

    def test_detects_localhost_as_local_runtime(self):
        self.assertTrue(_is_local_runtime_url("http://localhost:8501"))

    def test_local_persistence_defaults_to_off_when_runtime_is_unknown(self):
        with patch.dict(os.environ, {}, clear=False):
            self.assertFalse(_local_persistence_enabled())

    def test_local_persistence_can_be_enabled_explicitly(self):
        with patch.dict(os.environ, {"FLOOSY_ENABLE_LOCAL_PERSISTENCE": "1"}, clear=False):
            self.assertTrue(_local_persistence_enabled())


if __name__ == "__main__":
    unittest.main()
