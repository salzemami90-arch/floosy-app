import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.currency_localization import (
    currency_display_to_canonical_map,
    currency_matches,
    currency_option_label,
    currency_short_label,
)


class CurrencyLocalizationTests(unittest.TestCase):
    def test_arabic_currency_labels_do_not_expose_foreign_names(self):
        self.assertEqual(currency_option_label("¥ - 人民币", "ar"), "¥ - يوان صيني")
        self.assertEqual(currency_option_label("¥ - 円", "ar"), "¥ - ين ياباني")
        self.assertEqual(currency_option_label("S$ - SGD", "ar"), "S$ - دولار سنغافوري")

    def test_short_labels_use_unambiguous_codes_for_ltr_languages(self):
        self.assertEqual(currency_short_label("¥ - 人民币", "en"), "CNY")
        self.assertEqual(currency_short_label("¥ - 円", "en"), "JPY")
        self.assertEqual(currency_short_label("¥", "en"), "CNY")
        self.assertEqual(currency_short_label("S$ - SGD", "ms"), "SGD")

    def test_currency_matching_keeps_symbol_variant_compatibility(self):
        self.assertTrue(currency_matches("د.ك", "د.ك - دينار كويتي"))
        self.assertTrue(currency_matches("KWD", "د.ك - دينار كويتي"))
        self.assertFalse(currency_matches("¥ - 円", "¥ - 人民币"))

    def test_display_map_keeps_bare_yen_on_historic_cny_fallback(self):
        display_map = currency_display_to_canonical_map(["¥ - 人民币", "¥ - 円"], "en")

        self.assertEqual(display_map["¥"], "¥ - 人民币")
        self.assertEqual(display_map["JPY - Japanese Yen"], "¥ - 円")


if __name__ == "__main__":
    unittest.main()
