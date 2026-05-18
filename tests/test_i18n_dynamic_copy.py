import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.i18n import dashboard_brief_copy, format_i18n


class DynamicI18nCopyTests(unittest.TestCase):
    def test_korean_dynamic_dashboard_copy(self):
        brief = {
            "status": "stable",
            "message_ar": "الوضع المالي تحت السيطرة",
            "message_en": "Financial position is under control",
            "focus_label_ar": "صافي 90 يوم",
            "focus_label_en": "90-Day Net",
            "focus_value": 52.0,
            "support_label_ar": "يحتاج متابعة",
            "support_label_en": "Needs Follow-up",
            "support_value": 0.0,
            "projected_net": 52.0,
        }

        with patch("services.i18n.get_lang_code", return_value="ko"):
            message, detail, focus_label, support_label = dashboard_brief_copy(brief, "KWD")

        self.assertEqual(message, "재무 상황이 통제되고 있습니다")
        self.assertIn("예상 90일 순액", detail)
        self.assertEqual(focus_label, "90일 순액")
        self.assertEqual(support_label, "후속 확인 필요")

    def test_indonesian_selected_month_and_document_count(self):
        with patch("services.i18n.get_lang_code", return_value="id"):
            self.assertEqual(format_i18n("selected_month", month="Mei", year=2026), "Bulan terpilih: Mei 2026")
            self.assertEqual(format_i18n("document_count", count=2), "2 dokumen")


if __name__ == "__main__":
    unittest.main()
