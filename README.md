# Gemma 4 Developer Agent — Shakeup-Proof Submissions (`v20`–`v21`)

Private repository for audited, zero-leakage submission builders and bundles for the **Google - The Gemma 4 Developer Agent Competition** (Main 31B & Small Model E4B tracks).

## Audited Bundles
| Bundle | Model | `include_thoughts` | `thinking_budget` | Eval Budget | Leakage Audit | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `v20_main_31b` | `gemma-4-31b-it-qat-w4a16-ct` | `true` | `2048` | `28c / 7m / 60t` | CLEAN | Submitted (`58759418`, **0.15**) |
| `v20_small_e4b` | `gemma-4-e4b-it-qat-w4a16-ct` | `true` | `1536` | `24c / 6m / 52t` | CLEAN | Submitted (`58825231`, Running) |
| `v21_main_31b` | `gemma-4-31b-it-qat-w4a16-ct` | `true` | `3584` | `28c / 7m / 60t` | CLEAN | Ready for Nov 25 UTC |

## Rebuild & Validate
```bash
uv run --with pyyaml python build_v20.py
uv run --with pyyaml python build_v21.py
```
