import unittest

from config_floosy import _is_shared_hosted_url


class RuntimeDetectionTests(unittest.TestCase):
    def test_detects_streamlit_app_domain_as_shared_hosted(self):
        self.assertTrue(_is_shared_hosted_url("https://floosy-beta.streamlit.app"))

    def test_detects_share_streamlit_io_domain_as_shared_hosted(self):
        self.assertTrue(_is_shared_hosted_url("https://share.streamlit.io"))

    def test_localhost_is_not_shared_hosted(self):
        self.assertFalse(_is_shared_hosted_url("http://localhost:8501"))


if __name__ == "__main__":
    unittest.main()
