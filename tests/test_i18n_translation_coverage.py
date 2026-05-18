import ast
from pathlib import Path

from services.i18n import _TRANSLATIONS


LANG_CODES = {"zh", "ko", "ja", "id", "ms"}
SOURCE_PATHS = [
    Path("app.py"),
    *Path("pages_floosy").glob("*.py"),
    *Path("services").glob("*.py"),
]


def _literal_i18n_keys() -> dict[str, list[str]]:
    keys: dict[str, list[str]] = {}
    for path in SOURCE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name == "t" and len(node.args) >= 2:
                candidate = node.args[1]
            elif func_name == "translate_en" and node.args:
                candidate = node.args[0]
            else:
                continue

            if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str):
                keys.setdefault(candidate.value, []).append(f"{path}:{node.lineno}")
    return keys


def test_literal_ui_copy_has_all_non_english_translations():
    missing: list[str] = []
    partial: list[str] = []

    for key, refs in sorted(_literal_i18n_keys().items()):
        entry = _TRANSLATIONS.get(key)
        if entry is None:
            missing.append(f"{key!r} at {', '.join(refs[:3])}")
            continue

        missing_langs = sorted(LANG_CODES - set(entry))
        if missing_langs:
            partial.append(f"{key!r} missing {missing_langs} at {', '.join(refs[:3])}")

    assert not missing, "Missing i18n entries:\n" + "\n".join(missing)
    assert not partial, "Incomplete i18n entries:\n" + "\n".join(partial)
