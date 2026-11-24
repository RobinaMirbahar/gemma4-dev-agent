# Gemma 4 Autonomous SWE Agent: Zero-Leakage & Shakeup-Resistant Engineering

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://www.python.org/)
[![Audit](https://img.shields.io/badge/Leakage_Audit-Passing-brightgreen.svg)](audit_leakage.py)
[![Competition](https://img.shields.io/badge/Kaggle-Gemma_4_Developer_Agent-20BEFF.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent)

> **Empirical ablation study, zero-leakage submission pipeline, and public/private leaderboard shakeup analysis** for quantized (`W4A16`) thinking-model software engineering agents on **Google — The Gemma 4 Developer Agent Competition** (Main 31B & Small Model E4B tracks).

---

## Abstract

Deploying 4-bit quantized (`W4A16`) reasoning models as autonomous software engineering agents under strict hardware (`4 × NVIDIA L4`, `32,768`-token context ceiling) and ADK history-compaction (`14,336` tokens) constraints exposes three critical failure modes:

1. **Turn-to-Turn Reasoning Amnesia:** Disabling `include_thoughts` and starving `thinking_budget` (`1024`) caused a **-0.06** public-score regression (`0.18 → 0.12`). Restoring `include_thoughts: true` and scaling `thinking_budget` recovered **+0.03** immediately (`v20`, `0.15`), with `v21` (`TB=3584`) isolating near-native reasoning depth.
2. **Global Wall-Clock Timeout Cliff:** Over-allocating tool budgets (`40 calls / 8 min` at `TB=3072`) silently exhausted the global evaluation wall-clock. Bounding budgets to `28c / 7m / 60t` (31B) and `24c / 6m / 52t` (E4B) eliminates timeout failures.
3. **Public-Split Overfitting & Shakeup Risk:** On finite public evaluation splits ($N \in [50, 100]$), a 16-way tie at `0.24` vs. `0.18` lies inside the 95% Wilson confidence interval ($p > 0.35$). Removing repo-specific prompt heuristics and fixing `seed: 42` reduces private leaderboard variance.

Full statistical analysis and methodology are documented in **[TECHNICAL_REPORT.md](TECHNICAL_REPORT.md)**.

---

## Empirical Ablation Summary

| Version | Model Track | `include_thoughts` | `thinking_budget` | Budget | Zero-Leakage | Public Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `v4` | `gemma-4-31b-it-qat-w4a16-ct` | `true` | Native | `28c / 8m` | Baseline | **0.18** |
| `v17` | `gemma-4-31b-it-qat-w4a16-ct` | `true` | Native | `28c / 8m` | Contract-First | **0.17** |
| `v18` | `gemma-4-31b-it-qat-w4a16-ct` | `true` | `3072` | `40c / 8m` | Timeout Cliff | *No score* |
| `v19` | `gemma-4-31b-it-qat-w4a16-ct` | `false` | `1024` | `28c / 8m` | Amnesia | `0.12` |
| `v20` | `gemma-4-31b-it-qat-w4a16-ct` | `true` | `2048` | `28c / 7m` | **Verified (`seed=42`)** | **0.15** |
| **`v21`** | `gemma-4-31b-it-qat-w4a16-ct` | **`true`** | **`3584`** | **`28c / 7m`** | **Verified (`seed=42`)** | *Scheduled* |
| `v16` | `gemma-4-e4b-it-qat-w4a16-ct` | `true` | Native | Lean-6 | Baseline | **0.05** |
| `v18` | `gemma-4-e4b-it-qat-w4a16-ct` | `true` | `1536` | `36c / 8m` | Loop Drift | `0.03` |
| **`v20`** | `gemma-4-e4b-it-qat-w4a16-ct` | **`true`** | **`1536`** | **`24c / 6m`** | **Verified (`seed=42`)** | *Evaluating* |

---

## Repository Structure

```text
├── TECHNICAL_REPORT.md      # Full ablation study, Wilson CI shakeup analysis & methodology
├── audit_leakage.py         # Automated zero-leakage, brace-safety & ZIP integrity test suite
├── build_v20.py             # Deterministic builder for v20 (Main 31B & Small E4B)
├── build_v21.py             # Single-variable controlled ablation builder for v21 (Main 31B)
├── v20_main_31b/            # Audited v20 31B bundle & submission.zip
├── v20_small_e4b/           # Audited v20 E4B bundle & submission.zip
├── v21_main_31b/            # Audited v21 31B bundle & submission.zip
├── .github/workflows/       # Continuous Integration leakage & integrity verification
└── LICENSE                  # Apache 2.0 License
```

---

## Reproducibility & Automated Audit

```bash
# 1. Deterministically rebuild and validate bundles
uv run --with pyyaml python build_v20.py
uv run --with pyyaml python build_v21.py

# 2. Run the automated zero-leakage and ZIP integrity test suite
uv run python audit_leakage.py
```

---

## Citation

```bibtex
@misc{mirbahar2026gemma4swe,
  author       = {Robina Mirbahar},
  title        = {Zero-Leakage, Shakeup-Resistant Gemma 4 Autonomous SWE Agents},
  year         = {2026},
  howpublished = {\url{https://github.com/RobinaMirbahar/gemma4-dev-agent-submissions}}
}
```
