"""
Finding 2 chart (v2, post-challenge-round): Go8's funding premium per HDR
completion is not just an observed pattern - it is the direct, mechanical
consequence of the legislated RSP/RTP funding formulas, which weight R&D
income (which Go8 dominates far more than it dominates HDR completions).

Two panels:
  A. RBG $ per HDR completion, Go8 vs the rest of the sector, 2015-2024 -
     the gap is large AND stable across the decade (unchanged from v1).
  B. Mechanistic validation: Go8's share of RSP $ predicted from nothing but
     its HERDC income shares and the legislated 47%/53% formula weights,
     plotted against Go8's *actual* observed RSP share - the two track
     almost exactly, while Go8's HDR completions share sits far below both.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BLUE = "#2a78d6"
ORANGE = "#eb6834"
VIOLET = "#4a3aa7"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": INK,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})

m = pd.read_csv("data/clean/master_panel_v2.csv")
m = m[(m["Year"] >= 2015) & (m["Year"] <= 2024)].copy()
m["is_go8"] = (m["Cohort"] == "Go8").astype(int)

val = pd.read_csv("data/clean/go8_mechanism_validation.csv", index_col="Year")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))

# --- Panel A: $/completion, Go8 vs rest, over time ---
g = m.groupby(["Year", "is_go8"])[["hdr_completions", "rbg_total"]].sum().reset_index()
g["per_completion"] = g["rbg_total"] / g["hdr_completions"] / 1000
ax = axes[0]
for flag, color, label in [(1, BLUE, "Go8"), (0, ORANGE, "Rest of sector")]:
    d = g[g["is_go8"] == flag].sort_values("Year")
    ax.plot(d["Year"], d["per_completion"], color=color, linewidth=2.2, marker="o", markersize=4, label=label)
ax.set_ylabel(r"RBG \$ per HDR completion (\$'000)")
ax.set_title("A. The funding-per-completion gap is large and stable", fontsize=10.3, color=INK, loc="left", fontweight="bold")
ax.set_xticks(range(2015, 2025))
ax.set_xticklabels(range(2015, 2025), fontsize=8)
ax.legend(frameon=False, fontsize=9, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
ax.set_ylim(bottom=0)

# --- Panel B: predicted vs actual Go8 share of RSP $, plus HDR completions share for contrast ---
ax2 = axes[1]
ax2.plot(val.index, val["actual_rsp_go8_share"], color=BLUE, linewidth=2.4, marker="o", markersize=4, label="Go8 share of RSP $ (actual)")
ax2.plot(val.index, val["predicted_rsp_go8_share"], color=VIOLET, linewidth=2.0, linestyle="--", marker="s", markersize=3.5, label="Go8 share of RSP $ (predicted from\nincome shares + legislated formula)")
ax2.plot(val.index, val["hdr_completions_go8_share"], color=ORANGE, linewidth=2.2, marker="o", markersize=4, label="Go8 share of HDR completions")
ax2.set_ylabel("Go8 share of national total (%)")
ax2.set_title("B. The formula predicts the outcome; completions don't", fontsize=10.3, color=INK, loc="left", fontweight="bold")
ax2.set_xticks(range(2015, 2025))
ax2.set_xticklabels(range(2015, 2025), fontsize=8)
ax2.legend(frameon=False, fontsize=7.6, loc="center left", bbox_to_anchor=(0.0, 0.32))
ax2.spines[["top", "right"]].set_visible(False)
ax2.set_ylim(30, 78)

fig.tight_layout()
fig.savefig("charts/finding2_go8_premium.png", dpi=300, bbox_inches="tight")
print("saved charts/finding2_go8_premium.png")
