from pages_floosy.account_page import _build_filtered_df


def _sample_transactions():
    return [
        {
            "date": "2026-04-10",
            "type": "دخل",
            "amount": 50.0,
            "currency": "د.ك - دينار كويتي",
            "category": "راتب",
            "note": "راتب شرق أبريل",
            "payment_month_key": "2026-أبريل",
            "entitlement_month_key": "2026-مارس",
            "proof_name": "salary-slip.pdf",
            "proof_bytes": b"pdf",
            "source_template_name": "راتب شرق",
        },
        {
            "date": "2026-04-11",
            "type": "مصروف",
            "amount": 12.0,
            "currency": "د.ك - دينار كويتي",
            "category": "مشتريات",
            "note": "شراء أدوات",
            "payment_month_key": "2026-أبريل",
            "entitlement_month_key": "",
            "proof_name": "",
            "proof_bytes": b"",
            "source_template_name": "",
        },
    ]


def test_account_search_filters_by_proof_presence():
    df = _build_filtered_df(
        _sample_transactions(),
        currency="د.ك - دينار كويتي",
        query="",
        type_filter="الكل",
        category_filter="الكل",
        proof_filter="مع إثبات",
        newest_first=True,
    )
    assert len(df) == 1
    assert df.iloc[0]["proof_name"] == "salary-slip.pdf"

    df_no_proof = _build_filtered_df(
        _sample_transactions(),
        currency="د.ك - دينار كويتي",
        query="",
        type_filter="الكل",
        category_filter="الكل",
        proof_filter="بدون إثبات",
        newest_first=True,
    )
    assert len(df_no_proof) == 1
    assert df_no_proof.iloc[0]["category"] == "مشتريات"


def test_account_search_matches_source_template_name():
    df = _build_filtered_df(
        _sample_transactions(),
        currency="د.ك - دينار كويتي",
        query="شرق",
        type_filter="الكل",
        category_filter="الكل",
        proof_filter="الكل",
        newest_first=True,
    )
    assert len(df) == 1
    assert df.iloc[0]["source_template_name"] == "راتب شرق"


def test_account_search_category_filter_accepts_translated_label():
    df = _build_filtered_df(
        _sample_transactions(),
        currency="د.ك - دينار كويتي",
        query="",
        type_filter="الكل",
        category_filter="Salary",
        proof_filter="الكل",
        newest_first=True,
    )
    assert len(df) == 1
    assert df.iloc[0]["category"] == "راتب"
