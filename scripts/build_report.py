"""Build the PDF insight report: cover + Section 1 (<=3pp) + Section 2 (2pp) + Appendix (1pp)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfbase.pdfmetrics import stringWidth
import datetime

INK = colors.HexColor("#0b0b0b")
SECONDARY = colors.HexColor("#3d3d3a")
MUTED = colors.HexColor("#7a7972")
BLUE = colors.HexColor("#2a78d6")
RULE = colors.HexColor("#c3c2b7")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm

styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=13, leading=18, textColor=SECONDARY, spaceAfter=4),
    "cover_meta": ParagraphStyle("cover_meta", fontName="Helvetica", fontSize=11, leading=16, textColor=SECONDARY),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15.5, leading=19, textColor=INK, spaceBefore=4, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.3, leading=14, textColor=INK, spaceBefore=10, spaceAfter=5),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.4, leading=13.1, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.2, leading=12.6, textColor=INK, alignment=TA_JUSTIFY, leftIndent=10, spaceAfter=3.2, bulletIndent=0),
    "caption": ParagraphStyle("caption", fontName="Helvetica", fontSize=7.6, leading=10, textColor=MUTED, spaceBefore=3, spaceAfter=2),
    "source": ParagraphStyle("source", fontName="Helvetica-Oblique", fontSize=7.6, leading=10, textColor=MUTED, spaceBefore=2, spaceAfter=8),
    "finding_title": ParagraphStyle("finding_title", fontName="Helvetica-Bold", fontSize=13.5, leading=16.5, textColor=INK, spaceAfter=6),
    "footer": ParagraphStyle("footer", fontName="Helvetica", fontSize=8, leading=10, textColor=MUTED),
}


def rule(width=None, color=RULE, thickness=0.6, space_before=2, space_after=6):
    return HRFlowable(width=width or "100%", thickness=thickness, color=color, spaceBefore=space_before, spaceAfter=space_after)


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 12 * mm, "Research funding and HDR completions — insight report")
    canvas.drawRightString(PAGE_W - MARGIN, 12 * mm, f"{doc.page}")
    canvas.restoreState()


def cover_page(story):
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph("Research Funding and Higher Degree by Research Completions", styles["title"]))
    story.append(Paragraph("An analysis of Australian higher education providers, 2015–2024", styles["subtitle"]))
    story.append(Spacer(1, 10 * mm))
    story.append(rule(width=60 * mm, thickness=1.2, color=BLUE, space_before=0, space_after=10))
    story.append(Paragraph("Insight report — Research KPI Intern task", styles["cover_meta"]))
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph("Zareen Shyma", ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=13, textColor=INK, spaceAfter=2)))
    story.append(Paragraph("Zareen.Shyma@student.uts.edu.au", styles["cover_meta"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(datetime.date(2026, 9, 26).strftime("%-d %B %Y"), styles["cover_meta"]))
    story.append(PageBreak())


def section1(story):
    story.append(Paragraph("Section 1 — Data and Model", styles["h1"]))
    story.append(rule())

    story.append(Paragraph("1.1 Data sources", styles["h2"]))
    story.append(Paragraph(
        "This analysis uses two public data series published by the Australian Government Department of "
        "Education, plus one file provided directly for this task as an independent validation source.",
        styles["body"]))
    story.append(Paragraph(
        "• <b>Higher Education Statistics</b> (Student Data collection) — "
        "https://www.education.gov.au/higher-education-statistics — used for Higher Degree by Research "
        "(HDR) completions: Doctorate by Research + Master's by Research, by provider and year.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>Research block grant (RBG) allocations time series</b> — "
        "https://www.education.gov.au/research-block-grants/resources/research-block-grant-allocations-time-series "
        "— used for research funding: the Research Training Program (RTP) and Research Support Program (RSP), "
        "by provider and year, 2001–2026.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>Official HDR student completions time series (1989–2024)</b>, supplied directly by the task "
        "sponsor, used as an independent cross-check of the completions figures reconstructed from the Student "
        "Data publications (Section 1.3).",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>RSP/RTP calculation methodology</b> and the <b>R&amp;D income (HERDC) time series</b>, both published "
        "by the Dept. of Education under research-block-grants/resources, used in Section 2 Finding 2 to test "
        "whether the funding premium is mechanically explained by the legislated allocation formulas.",
        styles["bullet"]))

    story.append(Paragraph("1.2 Pipeline", styles["h2"]))
    story.append(Image("charts/pipeline_diagram.png", width=170 * mm, height=87 * mm))
    story.append(Paragraph(
        "Both raw sources needed non-trivial reconstruction before they could be joined: the RBG file is a clean "
        "tidy table, but the 2020–2024 completions figures existed only inside an Excel PivotTable, so the "
        "underlying record-level data had to be recovered from the workbook's pivot-cache XML; 2015–2019 "
        "completions came from five separate annual publications with inconsistent table numbering.",
        styles["body"]))

    story.append(Paragraph("1.3 Structural issues identified and resolved", styles["h2"]))
    story.append(Paragraph(
        "• <b>Provider name drift.</b> The same institution appears under different strings across years/files "
        "(CQUniversity vs. Central Queensland University; RMIT University vs. its RBG legal name Royal Melbourne "
        "Institute of Technology; Curtin University vs. Curtin University of Technology). Resolved with a canonical "
        "HEP-Code crosswalk anchored on the RBG file's provider list.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>2017 RBG program consolidation.</b> Six legacy programs (APA, IPRS, RTS, JRE, RIBG, SRE) were "
        "replaced by RTP and RSP in 2017. Resolved by aggregating to these two program families so the series is "
        "comparable before and after the reform.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>2021 COVID-19 anomaly.</b> RSP allocations roughly doubled in 2021 (a documented one-off $1bn "
        "pandemic support payment) while national HDR completions dipped, plausibly reflecting submission "
        "extensions. Both sides of the funding–completions relationship are affected in this single year, so "
        "2021 is excluded from the primary growth-rate specification (included as a robustness check).",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>Cell suppression.</b> Small counts in the legacy tables are masked ('&lt;5' / 'np'). Handled with "
        "documented interval-midpoint imputation, flagged per observation.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>Independent cross-check.</b> Comparing the reconstructed completions panel against the official "
        "HDR file (same HEP-Code scheme as the RBG file) showed a high overall level correlation (r=0.99) but "
        "material gaps concentrated in 2021 and a few other institution-years (e.g. Sydney −300, Melbourne "
        "−334). Diagnosis: the reconstructed panel's <i>total</i> (all-level) completions for these same "
        "institution-years matched an independently published all-level series almost exactly, so the crosswalk "
        "and overall counts were correct — the gap was specific to the Excel pivot tool's coarse course-level "
        "bucketing of HDR completions in COVID backlog-clearing years. The completions side of the panel was "
        "rebuilt directly from the official, purpose-built HDR file for the full analysis window; the RBG-side "
        "cleaning and crosswalk were unchanged. This cross-check is treated as a validation step for the panel-"
        "building methodology, not a limitation of it.",
        styles["bullet"]))

    story.append(Paragraph("1.4 Analytical approach", styles["h2"]))
    story.append(Paragraph(
        "The cleaned panel covers <b>43 providers × 2015–2024 (417 provider-years)</b>. Relationships are "
        "estimated with log-linear OLS carrying provider and year fixed effects and standard errors clustered by "
        "provider, both in levels (funding on completions, testing for a cross-sectional concentration premium) "
        "and in year-on-year growth rates (testing lead/lag dynamics at lags −3 to +3, both directions and "
        "contemporaneously). Findings are stress-tested against: dropping 2021; splitting RTP vs. RSP; adding "
        "total (all-level) completions as an alternative scale control; stratifying by mission group (Go8, ATN, "
        "IRU, RUN, non-aligned); and a leave-one-Go8-university-out check.",
        styles["body"]))

    story.append(Paragraph("1.5 Limitations", styles["h2"]))
    story.append(Paragraph(
        "• <b>Window length.</b> Ten annual observations per provider is short for detecting slow-moving "
        "dynamics; a relationship operating on a 3–5 year cycle (plausible given RTP's own multi-year formula) "
        "may not be visible in year-on-year growth rates even if it exists.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>Correlational, not causal.</b> Fixed effects remove level differences between providers and common "
        "shocks by year, but do not identify causal effects on their own — an unobserved provider-specific trend "
        "correlated with both funding and completions growth could still confound either finding.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>Small-provider suppression.</b> Cell-count masking in the legacy tables is concentrated among the "
        "smallest providers, who contribute little to the funding totals driving either finding, but their "
        "individual growth rates are noisier.",
        styles["bullet"]))
    story.append(Paragraph(
        "• <b>Forward changes not in scope.</b> The 2026 merger of the University of Adelaide and University of "
        "South Australia into “Adelaide University” falls outside the 2015–2024 window and does not affect "
        "either finding, but would need a crosswalk update before extending this panel forward.",
        styles["bullet"]))
    story.append(PageBreak())


def finding_page(story, kicker, title, image_path, img_w_mm, img_h_mm, paragraphs, source_note):
    story.append(Paragraph(kicker, ParagraphStyle("kicker", fontName="Helvetica-Bold", fontSize=9, textColor=BLUE, spaceAfter=2)))
    story.append(Paragraph(title, styles["finding_title"]))
    story.append(Image(image_path, width=img_w_mm * mm, height=img_h_mm * mm))
    story.append(Paragraph(source_note, styles["source"]))
    for p in paragraphs:
        story.append(Paragraph(p, styles["body"]))


def section2(story):
    story.append(Paragraph("Section 2 — Key Findings", styles["h1"]))
    story.append(rule())

    finding_page(
        story,
        "FINDING 1",
        "No statistically significant funding–completions dynamic detected — the apparent link is a scale artifact",
        "charts/finding1_no_dynamic_link.png", 168, 74,
        [
            "Raw provider-level correlation between RBG funding and HDR completions is high (r≈0.91) — the kind "
            "of number that invites a quick “funding drives completions” headline. It doesn't survive scrutiny. "
            "That correlation is measured in levels, where larger universities mechanically have more of "
            "everything: more funding, more completions, more staff, more students. It says nothing about "
            "whether a change in one precedes a change in the other.",
            "Testing the actual dynamic — does year-on-year funding growth lead, lag, or move with completions "
            "growth — removes the scale effect via provider and year fixed effects and tests lags −3 to +3 in "
            "both directions, plus the same-year relationship. Essentially none of it is significant: funding "
            "growth → next-year completions growth (coef=−0.33, p=0.39); completions growth → next-year "
            "funding growth (coef≈0.00, p=0.96); same-year (p=0.14). This holds with Total RBG or RTP alone, "
            "with/without 2021, and — tested after this draft was first reviewed — holds even more strongly "
            "on an extended 2001–2024 window (n=850 vs. 290, p=0.29–0.71 across variants). One isolated "
            "exception: the same-year relationship turns marginally significant (p=0.03, a negative coefficient) "
            "specifically when 2024 is excluded — not replicated in the lead specification or the extended "
            "window, and consistent with chance given the number of specifications tested.",
            "Panel A shows why: indexed to 2015, RBG funding climbs (and spikes sharply in the 2021 COVID top-up) "
            "while HDR completions grows on a materially different, choppier path — even a 69% one-year funding "
            "jump produced no matching movement in completions. Panel B shows the same result at the provider "
            "level: funding growth and next-year completions growth form a flat, uncorrelated cloud (r=0.03).",
            "<b>So what:</b> RTP's own allocation formula is explicitly a multi-year rolling average, not a "
            "same-year or one-year-lag mechanism — this result is consistent with that design, not a "
            "contradiction of it, but it means single-year funding movements are not a usable signal for "
            "forecasting near-term completions (or vice versa) at the provider level. Anyone building a KPI "
            "dashboard around annual funding-to-output tracking should not expect it to move in lockstep.",
        ],
        "Source: Dept. of Education RBG allocations time series; HDR completions time series (1989–2024). n=417 provider-years, 2015–2024 (n=850, 2001–2024 for the extended-window check).",
    )
    story.append(PageBreak())

    finding_page(
        story,
        "FINDING 2",
        "Go8's funding premium per completion is not about completions — it's the legislated formula's income weighting",
        "charts/finding2_go8_premium.png", 168, 74,
        [
            "Group of Eight (Go8) universities — 8 of the 43 providers in the panel — hold roughly 48% of the "
            "sector's HDR completions but 62–64% of RBG dollars, a gap that has held steady across all ten years "
            "and appears independently at every single Go8 university (1.56x–2.24x the non-Go8 $-per-completion "
            "average; not 2–3 outliers carrying the result).",
            "This is mechanical, not incidental. The Department's own legislated formulas (Other Grants Guidelines "
            "(Research) 2017; Higher Education Support (Commonwealth Scholarships) Guidelines 2025) show <b>RSP is "
            "47% competitive R&amp;D income share + 53% engagement income share — with zero HDR completions "
            "weighting</b>, while RTP is 25% + 25% income plus <b>50% weighted HDR completions</b>. Go8 holds "
            "~68.5% of national competitive income and ~64.2% of engagement income (2015–2024 avg.) — both far "
            "above its ~48% completions share. Reconstructing Go8's predicted RSP share from nothing but these "
            "income shares and the legislated weights reproduces its <i>actual</i> observed RSP share to within "
            "1–2 percentage points every year (Panel B) — the funding pattern is the formula working as "
            "designed, not a completions story at all.",
            "Consistent with this, the regression premium is <b>+124% in RSP</b> (p&lt;0.0001) but only <b>+21% in "
            "RTP</b> (p=0.10, n.s.) once HDR completions volume is controlled for — precisely because RTP's "
            "formula is half-diluted by a completions component RSP doesn't have. (Using total, not HDR-specific, "
            "completions as the control flips RTP significant too — the choice of denominator matters, and HDR "
            "completions is the one RTP's own formula actually uses.) Other mission groups (ATN, IRU, RUN) show no "
            "significant premium over non-aligned providers.",
            "<b>So what:</b> the popular reading — that Go8 dominates because it “out-produces” the sector on "
            "research training — gets this backwards. Go8's advantage is concentrated in R&amp;D income "
            "(competitive grants and industry engagement), a materially different policy lever than HDR training "
            "capacity. A funding-equity intervention aimed at completions would be aiming at the wrong mechanism.",
        ],
        "Source: Dept. of Education RBG allocations time series; HDR completions time series (1989–2024); R&amp;D income (HERDC) time series; RSP/RTP calculation guidance. n=417 provider-years, 2015–2024.",
    )
    story.append(PageBreak())


def appendix(story):
    story.append(Paragraph("Appendix", styles["h1"]))
    story.append(rule())
    story.append(Paragraph(
        "The full data pipeline, cleaning scripts, regression code, and chart-generation code for this report are "
        "published in a documented Git repository, including the reconciliation crosswalk, the pivot-cache "
        "reconstruction, and every robustness check referenced in Section 1.4. The repository also includes a "
        "three-page Power BI dashboard extending both findings with interactive slicers and provider-level detail "
        "(screenshots in the repository's README; no live web link, as this account's Power BI tenant has "
        "\"Publish to web\" disabled).",
        styles["body"]))
    story.append(Paragraph(
        "<b>Git repository:</b> https://github.com/mithizs08/UTS-Research-KPI-Analysis",
        styles["body"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Note on reproducibility: all figures in this report are computed directly from the two published "
        "Department of Education time series plus the official HDR completions file supplied for this task; no "
        "manual data entry was used. Suppressed-cell imputation and the 2021 COVID exclusion are documented "
        "choices, not silent adjustments — both are described in Section 1.3 and implemented as explicit, "
        "labelled steps in the repository code.",
        styles["body"]))


def build():
    doc = SimpleDocTemplate(
        "report/UTS_Research_KPI_Insight_Report.pdf",
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=18 * mm, bottomMargin=18 * mm,
        title="Research Funding and HDR Completions - Insight Report",
        author="Zareen Shyma",
    )
    story = []
    cover_page(story)
    section1(story)
    section2(story)
    appendix(story)
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


if __name__ == "__main__":
    build()
    print("built report/UTS_Research_KPI_Insight_Report.pdf")
