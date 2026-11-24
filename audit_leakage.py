"""Automated zero-leakage & integrity test suite for Gemma 4 Developer Agent submission bundles."""

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FORBIDDEN_TERMS = [
    "fastapi",
    "docs_src",
    "textualize",
    "rich",
    "starlette",
    "pydantic",
    "httpx",
    "robina",
    "c:/users",
    "f:/",
    "api_key",
    "secret",
    "kaggle.json",
    "tasks.jsonl",
    "swegemma",
]

EXPECTED_FILES = {
    "agent.yaml",
    "configs/sampling.yaml",
    "eval_config.yaml",
    "prompts/system.md",
}

BUNDLES = [
    "v20_main_31b/submission.zip",
    "v20_small_e4b/submission.zip",
    "v21_main_31b/submission.zip",
]


def audit_bundle(rel_path: str) -> None:
    zp = ROOT / rel_path
    assert zp.exists(), f"Missing bundle: {zp}"
    with zipfile.ZipFile(zp, "r") as zf:
        assert zf.testzip() is None, f"Corrupt ZIP: {zp}"
        assert set(zf.namelist()) == EXPECTED_FILES, f"Unexpected files in {zp}: {zf.namelist()}"
        for name in zf.namelist():
            text = zf.read(name).decode("utf-8")
            assert "\r\n" not in text, f"CRLF found in {zp}:{name}"
            low = text.lower()
            for term in FORBIDDEN_TERMS:
                assert term not in low, f"Leakage term '{term}' found in {zp}:{name}"
            if name == "prompts/system.md":
                braces = re.findall(r"\{[^}]*\}", text)
                assert braces == ["{problem_description}", "{hints?}"], f"Bad braces in {zp}: {braces}"
                stripped = text.replace("{problem_description}", "").replace("{hints?}", "")
                assert "{" not in stripped and "}" not in stripped, f"Stray brace in {zp}"
    print(f"[PASS] {rel_path}")


def main() -> None:
    for b in BUNDLES:
        audit_bundle(b)
    print("All bundles passed zero-leakage and integrity checks.")


if __name__ == "__main__":
    main()
