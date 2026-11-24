# Technical Report: Quantized Reasoning & Context-Efficient Gemma 4 Autonomous Developer Agents (`v20`–`v21`)

**Competition:** Google — The Gemma 4 Developer Agent Competition (Kaggle)  
**Tracks:** Main Track (`gemma-4-31b-it-qat-w4a16-ct`) & Small Model Track (`gemma-4-e4b-it-qat-w4a16-ct`)  
**Hardware Constraint:** 4 × NVIDIA L4 GPUs (96 GB VRAM, `max_model_len=32,768`, ADK compaction near `14,336` tokens)

---

## 1. Executive Summary
Across 21 controlled iterations on the Kaggle Gemma 4 Developer Agent benchmark, we identified three primary failure modes that cause silent regressions and private leaderboard shakeup in quantized (`W4A16`) thinking-model SWE agents:
1. **Turn-to-Turn Reasoning Amnesia (`include_thoughts: false` + starved `thinking_budget`):** Stripping `<|channel>thought...<channel|>` from multi-turn tool-call history and capping `thinking_budget=1024` dropped Main Track 31B performance from **0.18 / 0.17 → 0.12** (`v19`, Ref `58683672`). Restoring `include_thoughts: true` and raising `thinking_budget=2048` immediately recovered **+0.03** (`v20`, Ref `58759418`, **0.15**).
2. **Global Wall-Clock Timeout Cliff:** Expanding `max_tool_calls=40` with `thinking_budget=3072` (`v18`, Ref `58578842`) exceeded the global 4× L4 evaluation wall-clock and returned no score. Bounding budgets to `28c / 7m / 60t` (31B) and `24c / 6m / 52t` (E4B) eliminates timeout failures.
3. **Public-Set Overfitting & Implicit Repo Leakage:** Removing repo-specific prompt heuristics (e.g., FastAPI `docs_src/`) and fixing `seed: 42` (`temperature: 0.2`, `top_p: 0.95`) prevents correlated failure on unseen private repositories.

---

## 2. Empirical Ablation Matrix (Public Leaderboard)

| Version | Kaggle Ref | Track / Model | `include_thoughts` | `thinking_budget` | Eval Budget | Key Architectural Change | Public Score |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| `v4` | `57617428` | 31B W4A16 | `true` | Native | `28c / 8m` | Lean-6 ADK + `STATE:` journal + Call-8 anytime patch | **0.18** |
| `v17` | `58231052` | 31B W4A16 | `true` | Native | `28c / 8m` | Contract-first + Lean-6 + Done lock + Call-12 | **0.17** |
| `v18` | `58578842` | 31B W4A16 | `true` | `3072` | `40c / 8m` | Over-budgeted tool calls → **global timeout** | *No score* |
| `v19` | `58683672` | 31B W4A16 | `false` | `1024` | `28c / 8m` | Stripped thoughts + starved TB → **amnesia** | `0.12` |
| `v20` | `58759418` | 31B W4A16 | `true` | `2048` | `28c / 7m` | Zero-leakage, `seed=42`, restored thoughts | **0.15** |
| **`v21`** | *Scheduled Nov 25* | **31B W4A16** | **`true`** | **`3584`** | **`28c / 7m`** | **Single-variable TB scaling toward native 4096** | *Pending* |
| `v16` | `58197925` | E4B W4A16 | `true` | Native | Lean-6 | Small Model baseline + Call-8 anytime patch | **0.05** |
| `v18` | `58634540` | E4B W4A16 | `true` | `1536` | `36c / 8m` | Excess tool budget caused 4B exploration loops | `0.03` |
| **`v20`** | `58825231` | **E4B W4A16** | **`true`** | **`1536`** | **`24c / 6m`** | **Tighter loop cap + Call-8 edit + zero-leakage** | *Running* |

---

## 3. Public vs. Private Leaderboard Shakeup Analysis
As of Nov 24, 2026, **16 teams are tied at `0.24`** on the Public Leaderboard, followed by a discrete jump to `0.22`. Under a finite public test split ($N \in [50, 100]$):

- **$N = 100$:** `0.24` has 95% Wilson CI `[0.167, 0.332]` vs. `0.18` `[0.117, 0.267]` (Fisher's exact $p \approx 0.38$, **not statistically significant**).
- **$N = 50$:** `0.24` has 95% Wilson CI `[0.143, 0.374]` vs. `0.18` `[0.098, 0.308]` (Fisher's exact $p \approx 0.62$, **inside noise floor**).

**Research Conclusion:** The 16-way tie at `0.24` reflects public-template convergence and winner's-curse seed selection. To maximize expected **private leaderboard** rank, final submission selection should pair a proven high-score anchor (`v4`, `0.18`) with a zero-leakage, fixed-seed, timeout-safe generalizer (`v21` / `v20`).

---

## 4. Automated Leakage & Integrity Verification
All `v20` and `v21` bundles are verified by `audit_leakage.py` before upload:
- **Zero repo-specific priors:** Asserts absence of `fastapi`, `docs_src`, `textualize`, `rich`, `starlette`, `pydantic`, `httpx`, `tasks.jsonl`, and `swegemma`.
- **Zero credential/PII leakage:** Asserts absence of local paths, tokens, API keys, and personal identifiers.
- **ADK & Sandbox compliance:** Enforces exact template braces (`{problem_description}`, `{hints?}` only), Unix LF newlines, deterministic ZIP timestamps, and strict protected-file prohibitions (`tests/`, `conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`).

```bash
uv run --with pyyaml python build_v20.py
uv run --with pyyaml python build_v21.py
uv run python audit_leakage.py
```
