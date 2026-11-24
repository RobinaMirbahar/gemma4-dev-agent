"""Build and strictly validate v21_main_31b (single-variable controlled ablation over v20).

Controlled hypothesis (zero-leakage, anti-overfitting):
- v19 (TB=1024, include_thoughts=false, 28c/8m) -> 0.12
- v20 (TB=2048, include_thoughts=true,  28c/7m, seed=42, zero-leakage) -> 0.15 (+0.03)
- v21 (TB=3584, include_thoughts=true,  28c/7m, seed=42, zero-leakage) -> tests near-native 31B reasoning
  depth while keeping the exact timeout-safe 28c/7m/60t budget and zero-leakage prompt from v20.
"""

import hashlib
import re
import zipfile
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent

ALLOWED_MODELS = {
    "gemma-4-31b-it-qat-w4a16-ct",
    "gemma-4-12b-it-qat-w4a16-ct",
    "gemma-4-e4b-it-qat-w4a16-ct",
    "gemma-4-e2b-it-qat-w4a16-ct",
}
LEAN_6_TOOLS = [
    "run_command",
    "read_file",
    "edit_file",
    "write_file",
    "get_status",
    "submit_patch",
]

MAIN_31B_PROMPT = """You are an autonomous software engineer. Make the smallest correct change to SOURCE code in `/workspace` so hidden validation tests written from the issue pass. Exact names, types, messages, and edge cases in the issue are the literal contract.

# LIMITS & HYGIENE
- Budget: 28 tool calls, 7 minutes. An unedited tree scores zero.
- NEVER create, edit, or delete `tests/`, `test_*.py`, `*_test.py`, `conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, or `tox.ini`. NEVER run bare `pytest`, install packages, or look outside `/workspace`.
- History compacts near 14,336 tokens: ALWAYS pass `start_line` and `end_line` to `read_file` (40-75 lines max), pipe searches with `| head -20`, and never dump whole files.
- Before edits and after tests, emit one plain-text line: `STATE: <file:lines> | <cause> | <status>`

# PLAN
1. **Locate (Calls 1-7):** Extract exact symbols/errors from the issue. Use `git grep -n -F "symbol" -- "*.py" | head -20`, then read the target implementation + 1 caller or test. Check parallel implementations (`sync`/`async`, `Client`/`AsyncClient`, `@overload`, `__all__`) and update every twin.
2. **Edit by Call 10:** Apply the minimal fix with `edit_file` (`allow_multiple=false`). If unsure at Call 10, edit the best candidate anyway. Never repeat a failing `edit_file`: re-read the span and retry with a shorter unique `old_string` (or a quoted Python heredoc via `run_command` after 2 failures). Put scratch probes in `/tmp` via `run_command` only.
3. **Verify (1-2 calls):** After your last edit, run:
   `python3 -m py_compile <changed_py> && timeout 120 python3 -m pytest tests/path/test_x.py -x -q -k keyword --tb=short`
   (Fallback: `python3 -m unittest` or `timeout 30 python3 -c "..."`). Ignore unrelated pre-existing errors.
4. **Stop-Loss & Submit:** Keep 4 calls / 60s reserve (`get_status` and `submit_patch` are free). If 2 edits fail the same way, keep the cleanest compiling fix. Run `git status --short && git diff --stat`, clean any `/workspace` scratch files, call `submit_patch` once, verify `patch_size > 0`, then stop and reply `Done`.

## Task Specification
{problem_description}
{hints?}
"""


def make_agent_yaml(model_name: str) -> str:
    tools_block = "\n".join(f"  - {t}" for t in LEAN_6_TOOLS)
    return (
        "name: swe_agent\n"
        f"model: {model_name}\n"
        "instruction: !include prompts/system.md\n"
        "tools:\n"
        f"{tools_block}\n"
        "generate_content_config: !include configs/sampling.yaml\n"
    )


def make_sampling_yaml(max_output_tokens: int, thinking_budget: int) -> str:
    return (
        "temperature: 0.2\n"
        "top_p: 0.95\n"
        "seed: 42\n"
        f"max_output_tokens: {max_output_tokens}\n"
        "thinking_config:\n"
        f"  thinking_budget: {thinking_budget}\n"
        "  include_thoughts: true\n"
    )


def make_eval_yaml(max_tool_calls: int, max_time_minutes: int, max_turns: int) -> str:
    return (
        "evaluation:\n"
        "  timeout_seconds: 240\n"
        f"  max_tool_calls: {max_tool_calls}\n"
        f"  max_time_minutes: {max_time_minutes}\n"
        f"  max_turns: {max_turns}\n"
    )


def validate_and_package(
    bundle_name: str,
    files: dict[str, str],
    expected_model: str,
    max_prompt_bytes: int,
) -> tuple[Path, str, int]:
    out_dir = ROOT_DIR / bundle_name
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = out_dir / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    expected_keys = {
        "agent.yaml",
        "configs/sampling.yaml",
        "eval_config.yaml",
        "prompts/system.md",
    }
    assert set(files) == expected_keys
    for rel, content in files.items():
        assert "\r\n" not in content
        assert not Path(rel).is_absolute() and ".." not in Path(rel).parts
        target = bundle_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8"))

    class IncludeLoader(yaml.SafeLoader):
        pass

    def _include_ctor(loader: yaml.SafeLoader, node: yaml.Node):
        rel = loader.construct_scalar(node)
        target = (bundle_dir / rel).resolve()
        assert str(target).startswith(str(bundle_dir.resolve()))
        text = target.read_text(encoding="utf-8")
        return text if rel.endswith(".md") else yaml.safe_load(text)

    IncludeLoader.add_constructor("!include", _include_ctor)
    agent = yaml.load(files["agent.yaml"], Loader=IncludeLoader)
    eval_cfg = yaml.safe_load(files["eval_config.yaml"])["evaluation"]
    sampling = agent["generate_content_config"]

    assert agent["model"] == expected_model and agent["model"] in ALLOWED_MODELS
    assert agent["tools"] == LEAN_6_TOOLS
    assert "skills" not in agent and "sub_agents" not in agent and "adapter" not in agent
    assert sampling["seed"] == 42
    assert sampling["thinking_config"]["include_thoughts"] is True
    assert 0 < sampling["thinking_config"]["thinking_budget"] <= sampling["max_output_tokens"] <= 32768
    assert set(eval_cfg) == {"timeout_seconds", "max_tool_calls", "max_time_minutes", "max_turns"}

    prompt = agent["instruction"]
    prompt_bytes = len(prompt.encode("utf-8"))
    assert prompt_bytes <= max_prompt_bytes
    assert "fastapi" not in prompt.lower() and "docs_src" not in prompt.lower()
    braces = re.findall(r"\{[^}]*\}", prompt)
    assert braces == ["{problem_description}", "{hints?}"]
    stripped = prompt.replace("{problem_description}", "").replace("{hints?}", "")
    assert "{" not in stripped and "}" not in stripped

    zip_path = out_dir / "submission.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for rel in sorted(files):
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, files[rel].encode("utf-8"))

    with zipfile.ZipFile(zip_path, "r") as zf:
        assert zf.testzip() is None
        assert set(zf.namelist()) == expected_keys

    raw = zip_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    print(f"[PASS] {bundle_name}: {zip_path} ({len(raw):,} bytes | prompt={prompt_bytes:,}B | sha256={sha[:10]})")
    return zip_path, sha, len(raw)


def main() -> None:
    main_files = {
        "agent.yaml": make_agent_yaml("gemma-4-31b-it-qat-w4a16-ct"),
        "configs/sampling.yaml": make_sampling_yaml(max_output_tokens=8192, thinking_budget=3584),
        "eval_config.yaml": make_eval_yaml(max_tool_calls=28, max_time_minutes=7, max_turns=60),
        "prompts/system.md": MAIN_31B_PROMPT,
    }
    validate_and_package("v21_main_31b", main_files, "gemma-4-31b-it-qat-w4a16-ct", max_prompt_bytes=2200)


if __name__ == "__main__":
    main()
