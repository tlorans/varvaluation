# Handbook invitation — Design

**Date:** 2026-08-17
**Status:** Approved in conversation, then implemented on `handbook-invitation`.
**Repo:** `tlorans/varvaluation`

## Decisions

- **Artifact:** Research-program handbook (Tidy Finance analog). The paper is the spine, not the wrapper.
- **First reader:** A research student who might write the next paper.
- **First two minutes:** Value a ten-period unit claim two ways (fitted curve vs flat μ(1)). No downloads. Seed 7 prints μ(1)=2.37%, μ(10)=4.09%, flat PV +8.0% vs the curve.
- **Part 01 is the research program**, not Getting started.
- **Curriculum:** Program → Getting started → Joint system → Measurement (public data before WRDS) → What moved the return → Firms. Valuator page is a side path under Firms.
- **Voice:** Invitation first, honesty later. Sample limits live at the end of Firms. Forbidden first sentences: “This is an exposition…”, “This section is a software demonstration…”, “What this is not competing with…”.
- **Chrome:** MkDocs Material. Part kicker, one-sentence You will, wider column, `navigation.footer`. No testimonials, no second language, no new site generator.
- **No package API change.**

## File map

Create: `docs/guide/program.md`, `docs/guide/start.md`, `examples/flat_vs_curve.py`, `tests/test_flat_vs_curve.py`.

Landing: `docs/index.md`. Nav and chrome: `mkdocs.yml`, `docs/stylesheets/extra.css`. README matches the landing.
