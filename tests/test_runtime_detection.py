import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config_floosy import (
    _apply_browser_language_preference,
    _apply_browser_query_preferences,
    _hosted_data_warning_state,
    _is_local_runtime_url,
    _is_shared_hosted_url,
    _local_persistence_enabled,
    _preferred_language_from_accept_language,
    get_month_selection,
)


class RuntimeDetectionTests(unittest.TestCase):
    def test_settings_page_uses_selectable_month_controls(self):
        class FakeSidebar:
            def __init__(self):
                self.selectboxes = []

            def markdown(self, *_args, **_kwargs):
                return None

            def subheader(self, *_args, **_kwargs):
                return None

            def selectbox(self, label, options, index=0, *_args, **_kwargs):
                self.selectboxes.append((label, list(options), index))
                return options[index]

        fake_sidebar = FakeSidebar()
        fake_st = SimpleNamespace(
            session_state={"settings": {"language": "English"}},
            sidebar=fake_sidebar,
        )

        with patch("config_floosy.st", fake_st):
            month_key, month, year = get_month_selection("settings")

        self.assertIsInstance(month_key, str)
        self.assertIsInstance(month, str)
        self.assertIsInstance(year, int)
        self.assertEqual(len(fake_sidebar.selectboxes), 2)

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

    def test_hosted_warning_requires_cloud_login_when_configured(self):
        self.assertEqual(
            _hosted_data_warning_state("https://floosy-beta.streamlit.app", cloud_configured=True, cloud_logged_in=False),
            "cloud_login_required",
        )

    def test_hosted_warning_requires_setup_when_cloud_not_configured(self):
        self.assertEqual(
            _hosted_data_warning_state("https://floosy-beta.streamlit.app", cloud_configured=False, cloud_logged_in=False),
            "cloud_setup_required",
        )

    def test_hosted_warning_disappears_when_cloud_is_logged_in(self):
        self.assertEqual(
            _hosted_data_warning_state("https://floosy-beta.streamlit.app", cloud_configured=True, cloud_logged_in=True),
            "",
        )

    def test_local_runtime_has_no_hosted_warning(self):
        self.assertEqual(
            _hosted_data_warning_state("http://localhost:8501", cloud_configured=False, cloud_logged_in=False),
            "",
        )

    def test_accept_language_prefers_english_when_browser_is_english(self):
        self.assertEqual(_preferred_language_from_accept_language("en-US,en;q=0.9,ar;q=0.8"), "English")

    def test_accept_language_prefers_arabic_when_browser_is_arabic(self):
        self.assertEqual(_preferred_language_from_accept_language("ar-KW,ar;q=0.9,en;q=0.8"), "العربية")

    def test_browser_language_applies_when_user_has_not_selected_language(self):
        fake_st = SimpleNamespace(
            context=SimpleNamespace(headers={"accept-language": "en-US,en;q=0.9"}),
            session_state={"settings": {"language": "العربية", "language_user_selected": False}},
        )
        with patch("config_floosy.st", fake_st):
            _apply_browser_language_preference()
        self.assertEqual(fake_st.session_state["settings"]["language"], "English")

    def test_browser_language_does_not_override_manual_selection(self):
        fake_st = SimpleNamespace(
            context=SimpleNamespace(headers={"accept-language": "en-US,en;q=0.9"}),
            session_state={"settings": {"language": "العربية", "language_user_selected": True}},
        )
        with patch("config_floosy.st", fake_st):
            _apply_browser_language_preference()
        self.assertEqual(fake_st.session_state["settings"]["language"], "العربية")

    def test_query_preferences_restore_language_and_mark_welcome_complete(self):
        fake_st = SimpleNamespace(
            query_params={
                "f_w": "1",
                "f_lang": "en",
            },
            session_state={"settings": {"language": "العربية", "language_user_selected": False, "name": ""}},
        )
        with patch("config_floosy.st", fake_st):
            _apply_browser_query_preferences()
        self.assertEqual(fake_st.session_state["settings"]["language"], "English")
        self.assertTrue(fake_st.session_state["settings"]["language_user_selected"])
        self.assertTrue(fake_st.session_state["_welcome_completed"])


if __name__ == "__main__":
    unittest.main()
