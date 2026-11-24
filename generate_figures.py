"""Generate 300-DPI publication-grade architecture and empirical ablation figures."""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUT_DIR = Path(__file__).resolve().parent / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#CBD5E1",
    "axes.linewidth": 1.0,
})


def make_architecture_diagram() -> None:
    fig, ax = plt.subplots(figsize=(13, 6.2), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    # Title
    ax.text(
        6.5, 5.82,
        "Gemma 4 Autonomous SWE Agent — System Architecture (4 × NVIDIA L4, Offline Sandbox)",
        ha="center", va="center", fontsize=13.5, fontweight="bold", color="#0F172A"
    )
    ax.text(
        6.5, 5.48,
        "W4A16 Quantized Reasoning + ADK Compaction Hygiene + Bounded Lean-6 Tool Execution",
        ha="center", va="center", fontsize=9.5, color="#475569"
    )

    def draw_box(x, y, w, h, title, body, fc, ec, title_color="#0F172A"):
        box = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.12,rounding_size=0.14",
            facecolor=fc, edgecolor=ec, linewidth=1.6
        )
        ax.add_patch(box)
        ax.text(x + w / 2, y + h - 0.30, title, ha="center", va="center",
                fontsize=10, fontweight="bold", color=title_color)
        ax.text(x + w / 2, y + (h - 0.48) / 2, body, ha="center", va="center",
                fontsize=8.3, color="#334155", linespacing=1.45)

    # 1. Task & Contract
    draw_box(
        0.35, 3.35, 2.7, 1.75,
        "1. Task Specification",
        "Issue Description + Hints\nLiteral Contract Extraction\n(Symbols, Types, Edge Cases)\nRepo-Agnostic Prompt (<2.2 KB)",
        "#EFF6FF", "#2563EB", "#1D4ED8"
    )

    # 2. vLLM Reasoning Engine
    draw_box(
        3.65, 3.35, 3.4, 1.75,
        "2. vLLM Engine (4 × L4, TP=4)",
        "Gemma 4 31B / E4B (W4A16-CT)\nmax_model_len = 32,768\ninclude_thoughts = true\nTB = 2048–3584 | seed = 42, T = 0.2",
        "#F5F3FF", "#7C3AED", "#6D28D9"
    )

    # 3. ADK Compaction & State Guard
    draw_box(
        7.65, 3.35, 2.45, 1.75,
        "3. ADK Context Guard",
        "Compaction @ 14,336 tok\nBounded Reads (40–75 L)\nSTATE: <file|cause|status>\nCall-8/10 Anytime Patch",
        "#FEF3C7", "#D97706", "#B45309"
    )

    # 4. Lean-6 Tool Layer
    draw_box(
        10.6, 3.35, 2.05, 1.75,
        "4. Lean-6 Tools",
        "run_command\nread_file / edit_file\nwrite_file\nget_status / submit_patch",
        "#ECFDF5", "#059669", "#047857"
    )

    # Bottom: Air-Gapped Execution & Verification Loop
    draw_box(
        0.35, 0.55, 5.7, 2.05,
        "5. Air-Gapped /workspace Sandbox & Protected-File Gate",
        "• Locate via `git grep -n -F` (head -20) + bounded `read_file` slices\n"
        "• Minimal source-only patch via `edit_file` (allow_multiple=false)\n"
        "• Strict Guard: NEVER modify tests/, conftest.py, pytest.ini, pyproject.toml\n"
        "• Compile + Targeted Verification: `py_compile` && `timeout 120 pytest -x -q -k`",
        "#F8FAFC", "#475569", "#0F172A"
    )

    draw_box(
        6.65, 0.55, 6.0, 2.05,
        "6. Budget Controller & Single-Shot Patch Submission",
        "• Main 31B Budget: 28 tool calls | 7 min | 60 turns | 240s cmd timeout\n"
        "• Small E4B Budget: 24 tool calls | 6 min | 52 turns | Call-8 edit lock\n"
        "• Stop-Loss Reserve: 4 calls / 60s reserved for `git diff --stat` & cleanup\n"
        "• Terminal Gate: `submit_patch` once -> verify `patch_size > 0` -> `Done`",
        "#FFF1F2", "#E11D48", "#BE123C"
    )

    # Arrows top row
    arrow_kw = dict(arrowstyle="-|>,head_length=0.6,head_width=0.35", lw=1.8, color="#475569")
    ax.annotate("", xy=(3.60, 4.22), xytext=(3.10, 4.22), arrowprops=arrow_kw)
    ax.annotate("", xy=(7.60, 4.22), xytext=(7.10, 4.22), arrowprops=arrow_kw)
    ax.annotate("", xy=(10.55, 4.22), xytext=(10.15, 4.22), arrowprops=arrow_kw)

    # Loop arrows down & across
    ax.annotate("", xy=(11.62, 2.68), xytext=(11.62, 3.30), arrowprops=arrow_kw)
    ax.annotate("", xy=(6.12, 1.58), xytext=(6.60, 1.58),
                arrowprops=dict(arrowstyle="<->,head_length=0.55,head_width=0.32", lw=1.8, color="#475569"))
    ax.annotate("", xy=(5.35, 3.30), xytext=(5.35, 2.68),
                arrowprops=dict(arrowstyle="-|>,head_length=0.6,head_width=0.35", lw=1.8, color="#7C3AED", ls="--"))
    ax.text(5.48, 2.98, "Multi-turn\nObservation", fontsize=7.8, color="#6D28D9", va="center")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "architecture_pipeline.png", dpi=300, bbox_inches="tight")
    plt.close()


def wilson_ci(p: float, n: int = 100, z: float = 1.96) -> tuple[float, float]:
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def make_ablation_chart() -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8), dpi=300, gridspec_kw={"width_ratios": [1.35, 1]})
    fig.patch.set_facecolor("#FFFFFF")

    # Panel A: 31B Reasoning & Budget Ablation
    labels = [
        "v19\n(TB=1024,\nthoughts=off)",
        "v20\n(TB=2048,\nthoughts=on)",
        "v17\n(Native TB,\n28c/8m)",
        "v4\n(Native TB,\nCall-8 Patch)",
    ]
    scores = [0.12, 0.15, 0.17, 0.18]
    colors = ["#EF4444", "#3B82F6", "#10B981", "#059669"]
    cis = [wilson_ci(s, 100) for s in scores]
    yerr = np.array([[s - lo for s, (lo, _) in zip(scores, cis)],
                     [hi - s for s, (_, hi) in zip(scores, cis)]])

    x = np.arange(len(labels))
    bars = ax1.bar(x, scores, width=0.55, color=colors, alpha=0.9, edgecolor="#0F172A", linewidth=0.8)
    ax1.errorbar(x, scores, yerr=yerr, fmt="none", ecolor="#334155", elinewidth=1.3, capsize=4)

    for bar, s in zip(bars, scores):
        ax1.text(bar.get_x() + bar.get_width() / 2, s + 0.008, f"{s:.2f}",
                 ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#0F172A")

    ax1.set_title("A. Main Track (Gemma 4 31B W4A16) — Reasoning Ablation", fontsize=11, fontweight="bold", color="#0F172A", pad=10)
    ax1.set_ylabel("Public Solve Rate (with 95% Wilson CI, N=100)", fontsize=9.2, color="#334155")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=8.5, color="#1E293B")
    ax1.set_ylim(0, 0.30)
    ax1.grid(axis="y", linestyle="--", alpha=0.45, color="#94A3B8")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.annotate("v18 (40c / TB=3072)\nGlobal Timeout Cliff",
                 xy=(2.5, 0.255), ha="center", fontsize=8.2, color="#B91C1C",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#EF4444", lw=1))

    # Panel B: Small Model Track (E4B)
    e4b_labels = ["v18 E4B\n(36c / 8m\nLoop Drift)", "v16 E4B\n(Lean-6 +\nCall-8 Patch)"]
    e4b_scores = [0.03, 0.05]
    e4b_colors = ["#F59E0B", "#0EA5E9"]
    e4b_cis = [wilson_ci(s, 100) for s in e4b_scores]
    e4b_yerr = np.array([[s - lo for s, (lo, _) in zip(e4b_scores, e4b_cis)],
                         [hi - s for s, (_, hi) in zip(e4b_scores, e4b_cis)]])

    x2 = np.arange(len(e4b_labels))
    bars2 = ax2.bar(x2, e4b_scores, width=0.48, color=e4b_colors, alpha=0.9, edgecolor="#0F172A", linewidth=0.8)
    ax2.errorbar(x2, e4b_scores, yerr=e4b_yerr, fmt="none", ecolor="#334155", elinewidth=1.3, capsize=4)

    for bar, s in zip(bars2, e4b_scores):
        ax2.text(bar.get_x() + bar.get_width() / 2, s + 0.005, f"{s:.2f}",
                 ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#0F172A")

    ax2.set_title("B. Small Model Track (Gemma 4 E4B W4A16)", fontsize=11, fontweight="bold", color="#0F172A", pad=10)
    ax2.set_ylabel("Public Solve Rate (95% Wilson CI)", fontsize=9.2, color="#334155")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(e4b_labels, fontsize=8.8, color="#1E293B")
    ax2.set_ylim(0, 0.14)
    ax2.grid(axis="y", linestyle="--", alpha=0.45, color="#94A3B8")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.annotate("v20 E4B (24c/6m, seed=42)\nEvaluating (Ref 58825231)",
                 xy=(0.5, 0.115), ha="center", fontsize=8.2, color="#0369A1",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#F0F9FF", ec="#0EA5E9", lw=1))

    plt.tight_layout()
    plt.savefig(OUT_DIR / "thinking_budget_ablation.png", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    make_architecture_diagram()
    make_ablation_chart()
    print("[PASS] Generated 300-DPI figures in", OUT_DIR)
