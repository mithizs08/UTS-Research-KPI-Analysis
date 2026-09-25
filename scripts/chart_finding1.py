"""
Finding 1 chart: the naive levels relationship between RBG funding and HDR
completions is a scale artifact - growth rates show no reliable lead/lag.

Two panels, one shared story:
  A. National totals indexed to 2015=100 - funding climbs smoothly, HDR
     completions do not track it step for step (avoids a dual-axis chart by
     indexing both series to a common base, per dataviz guidance).
  B. Provider-level year-on-year growth: RBG $ growth (x) vs next-year HDR
     completions growth (y), all 43 providers x up to 9 transitions. The
     near-flat fit line and low R^2 is the same "no relationship" result as
     the panel-regression (coef=-0.33, p=0.39), shown visually.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- validated palette (light mode) ---
BLUE = "#2a78d6"
ORANGE = "#eb6834"
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

fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))

# --- Panel A: indexed national totals ---
nat = m.groupby("Year")[["hdr_completions", "rbg_total"]].sum().sort_index()
idx = nat / nat.loc[2015] * 100
ax = axes[0]
ax.plot(idx.index, idx["rbg_total"], color=BLUE, linewidth=2.2, marker="o", markersize=4, label="Total RBG funding ($)")
ax.plot(idx.index, idx["hdr_completions"], color=ORANGE, linewidth=2.2, marker="o", markersize=4, label="HDR completions")
ax.axvspan(2020.6, 2021.4, color=GRID, alpha=0.6, zorder=0)
ax.text(2021, 135, "COVID\nyear", ha="center", va="center", fontsize=8, color=MUTED)
ax.set_ylabel("Index (2015 = 100)")
ax.set_title("A. National totals move on different paths", fontsize=11, color=INK, loc="left", fontweight="bold")
ax.set_xticks(range(2015, 2025))
ax.set_xticklabels(range(2015, 2025), rotation=0, fontsize=8)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)

# --- Panel B: growth-rate scatter, funding growth(t) vs completions growth(t+1) ---
m = m.sort_values(["HEP_Code", "Year"])
m["log_hdr"] = np.log(m["hdr_completions"].clip(lower=1))
m["log_rbg"] = np.log(m["rbg_total"].clip(lower=1))
m["g_hdr"] = m.groupby("HEP_Code")["log_hdr"].diff()
m["g_rbg"] = m.groupby("HEP_Code")["log_rbg"].diff()
gm = m[m["Year"] != 2021].copy()
gm["g_hdr_lead1"] = gm.groupby("HEP_Code")["g_hdr"].shift(-1)
d = gm.dropna(subset=["g_rbg", "g_hdr_lead1"])
d = d[(d["g_rbg"].abs() < 2) & (d["g_hdr_lead1"].abs() < 2)]  # drop tiny-base outliers for readability

ax2 = axes[1]
ax2.scatter(d["g_rbg"] * 100, d["g_hdr_lead1"] * 100, s=18, color=BLUE, alpha=0.45, edgecolors="none")
b, a = np.polyfit(d["g_rbg"], d["g_hdr_lead1"], 1)
xs = np.linspace(d["g_rbg"].min(), d["g_rbg"].max(), 50)
ax2.plot(xs * 100, (a + b * xs) * 100, color=ORANGE, linewidth=2.2)
r = d["g_rbg"].corr(d["g_hdr_lead1"])
ax2.axhline(0, color=BASELINE, linewidth=0.8)
ax2.axvline(0, color=BASELINE, linewidth=0.8)
ax2.set_xlabel("Funding growth, year t (%)")
ax2.set_ylabel("HDR completions growth, year t+1 (%)")
ax2.set_title(f"B. No lead/lag relationship (r = {r:.2f})", fontsize=11, color=INK, loc="left", fontweight="bold")
ax2.spines[["top", "right"]].set_visible(False)
ax2.text(0.97, 0.03, "provider-year observations, 2015–2024\n(2021 excluded; fixed-effects\nregression: p = 0.39)",
          transform=ax2.transAxes, ha="right", va="bottom", fontsize=7.5, color=MUTED)

fig.tight_layout()
fig.savefig("charts/finding1_no_dynamic_link.png", dpi=300, bbox_inches="tight")
print("saved charts/finding1_no_dynamic_link.png")
