"""Data pipeline diagram for Section 1."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"
INK = "#0b0b0b"
MUTED = "#898781"
SURFACE = "#fcfcfb"
BOXBG = "#ffffff"

fig, ax = plt.subplots(figsize=(11, 5.6))
ax.set_xlim(0, 11)
ax.set_ylim(0, 5.6)
ax.axis("off")
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)


def box(x, y, w, h, text, color, fontsize=8.6, text_color=INK):
    fb = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                         linewidth=1.4, edgecolor=color, facecolor=BOXBG, zorder=2)
    ax.add_patch(fb)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
            color=text_color, zorder=3, linespacing=1.35)


def arrow(x1, y1, x2, y2, color=MUTED):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                         linewidth=1.4, color=color, zorder=1)
    ax.add_patch(a)


# Row 1: raw sources
box(0.2, 4.5, 2.5, 0.9, "HE Student Data\n(Dept. of Education)\nSection 14 .xls/.xlsx,\n2015–2019 + pivot 2020–2024", BLUE)
box(3.0, 4.5, 2.5, 0.9, "Official HDR completions\ntime series 1989–2024\n(cross-check source)", AQUA)
box(5.8, 4.5, 2.5, 0.9, "RBG allocations\ntime series 2001–2026\n(Dept. of Education)", ORANGE)

# Row 2: cleaning steps
box(0.2, 3.1, 2.5, 1.0, "Reverse-engineer pivot\ncache (2020–2024);\nparse legacy tables\n(2015–2019)", BLUE, fontsize=8.2)
box(3.0, 3.1, 2.5, 1.0, "Used to validate &\nreplace HDR figures\nafter cross-check\nrevealed a gap", AQUA, fontsize=8.2)
box(5.8, 3.1, 2.5, 1.0, "Aggregate to program\nfamilies; COVID-adjust\n2021 RSP; flag 2017\nprogram consolidation", ORANGE, fontsize=8.2)

arrow(1.45, 4.5, 1.45, 4.1)
arrow(4.25, 4.5, 4.25, 4.1)
arrow(7.05, 4.5, 7.05, 4.1)

# Row 3: crosswalk
box(1.6, 1.85, 5.6, 0.85, "Canonical HEP-Code crosswalk\n(resolves name drift: CQUniversity/Central Queensland Uni,\nRMIT/Royal Melbourne Inst. of Technology, etc.)", VIOLET, fontsize=8.6)
arrow(1.45, 3.1, 3.6, 2.7)
arrow(4.25, 3.1, 4.4, 2.7)
arrow(7.05, 3.1, 5.4, 2.7)

# Row 4: master panel (solid black box, drawn directly - no white underlay)
mp = FancyBboxPatch((1.6, 0.75), 5.6, 0.7, boxstyle="round,pad=0.02,rounding_size=0.08",
                     linewidth=0, facecolor=INK, zorder=2)
ax.add_patch(mp)
ax.text(1.6 + 5.6 / 2, 0.75 + 0.35, "Master panel: 43 providers × 2015–2024 (417 provider-years)",
        ha="center", va="center", fontsize=9.4, color="white", zorder=3)
arrow(4.4, 1.85, 4.4, 1.45)

# Right column: analysis
box(8.3, 3.1, 2.5, 2.3, "Analysis\n\n• Panel regressions,\n  provider + year FE\n• Growth-rate lead/lag\n  (lags −3..+3)\n• Cohort stratification\n• Leave-one-out checks", VIOLET, fontsize=8.0)
arrow(7.2, 1.1, 8.4, 3.05)

fig.text(0.01, 0.01, "Grey arrows show data flow; the cross-check (aqua) fed back into the completions branch after a discrepancy was found and diagnosed (see Section 1.3).",
          fontsize=7.3, color=MUTED)

fig.tight_layout()
fig.savefig("charts/pipeline_diagram.png", dpi=300, bbox_inches="tight")
print("saved charts/pipeline_diagram.png")
