"""Generate the Benchmark-Forge architecture diagram (GitHub-dark style).

Run:  python assets/generate_architecture_diagram.py
Output: assets/architecture_diagram.png

This is a documentation asset only — it is NOT required to run the agent
pipeline (the agents use only the standard library + pytest).
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless / sandbox safe
import matplotlib.pyplot as plt

FIG_BG = "#0d1117"
NODE_BG = "#161b22"
NODE_EDGE = "#30363d"
AGENT_BG = "#1f6feb"
AGENT_EDGE = "#58a6ff"
VERIFY_BG = "#238636"
VERIFY_EDGE = "#2ea043"
OK_FG = "#3fb950"
MUTED = "#8b949e"
FAIL_FG = "#f85149"


def main(path: str = "assets/architecture_diagram.png") -> None:
    fig, ax = plt.subplots(figsize=(11, 4), facecolor=FIG_BG)
    ax.set_facecolor(FIG_BG)
    ax.axis("off")

    boxes = [
        ("Bug Report /\nCode Snippet", 0.10, 0.5, NODE_BG, NODE_EDGE, "#c9d1d9"),
        ("Extractor Agent\n(Structured JSON)", 0.33, 0.5, AGENT_BG, AGENT_EDGE, "#ffffff"),
        ("Test Generator\n(Pytest Module)", 0.60, 0.5, AGENT_BG, AGENT_EDGE, "#ffffff"),
        ("Verifier Agent\n(Sandbox Pytest)", 0.86, 0.5, VERIFY_BG, VERIFY_EDGE, "#ffffff"),
    ]
    for text, x, y, bg, ec, tc in boxes:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            color=tc,
            fontsize=9,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.6", facecolor=bg, edgecolor=ec, linewidth=2),
        )

    # Horizontal flow arrows
    ax.annotate("", xy=(0.22, 0.5), xytext=(0.17, 0.5),
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=2))
    ax.annotate("", xy=(0.48, 0.5), xytext=(0.43, 0.5),
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=2))
    ax.annotate("", xy=(0.74, 0.5), xytext=(0.70, 0.5),
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=2))

    ax.text(0.20, 0.57, "input", ha="center", color=MUTED, fontsize=8)
    ax.text(0.45, 0.57, "problem JSON", ha="center", color=MUTED, fontsize=8)
    ax.text(0.72, 0.57, "test module", ha="center", color=MUTED, fontsize=8)

    # Feedback loop (fail -> retry) from Verifier back to Generator
    ax.annotate(
        "fail (stderr) -> Retry loop (max 3)",
        xy=(0.60, 0.73),
        xytext=(0.86, 0.73),
        ha="center",
        va="bottom",
        color=FAIL_FG,
        fontsize=8,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=FAIL_FG, lw=1.5, connectionstyle="arc3,rad=-0.4"),
    )

    # Success output below Verifier
    ax.annotate("pass", xy=(0.86, 0.28), xytext=(0.86, 0.38),
                ha="center", color=OK_FG, fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=OK_FG, lw=2))
    ax.text(
        0.86,
        0.16,
        "Final Verified Suite",
        ha="center",
        va="center",
        color=OK_FG,
        fontsize=9,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=NODE_BG, edgecolor=OK_FG, linewidth=1.5),
    )

    plt.tight_layout()
    fig.savefig(path, dpi=300, facecolor=FIG_BG, edgecolor="none")
    print(f"Saved {path} successfully.")


if __name__ == "__main__":
    main()
