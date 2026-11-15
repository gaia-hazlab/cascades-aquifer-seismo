# Project instructions

## Purpose

Test the Cascade crest volcanic aquifer hypothesis (Karlstrom et al. 2025, PNAS)
with seismology. Denolle Lab (UW) and Karlstrom group (University of Oregon).
The organising plan is joint data assimilation into a groundwater model
(`docs/05_assimilation_design.md`, draft): compare a deep-reservoir model class
against a shallow-only class on all available data. Two questions, kept
separate in code and prose:

1. **Existence and extent**: static Vp/Vs and resistivity, validated at drill holes.
2. **Function**: time-lapse dv/v response time and band dependence, plus
   hydroseismicity, as an old-rock vs young-rock contrast across Santiam Pass.

Mount St. Helens (MSH) is the method-calibration site. Results there are not
evidence for or against the Oregon aquifer; never write them up as such.
Read `README.md`, `docs/00_critique_and_reframe.md` and `HANDOFF.md` before
changing anything.

## Trust levels

- Verified, under regression test (`tests/test_synthetic.py`): `forward/*`,
  `modflow/*`, `analysis/phase_test.py --selftest`, `pipeline/dvv_stretch.py`.
- Written but not run against live services: `pipeline/01`–`03`.
  `03_snotel.py` (NRCS report-generator URL) is the least certain.
- Priors, not facts: beta0 (one dynamic measurement, Taira & Brenguier 2016,
  so an upper bound), the +15 % Vp gain on saturation, Sy and fracture
  porosity, the 2-D hillslope geometry.

Every number in `docs/` is a literature value or a synthetic result unless it
cites a data file and command. Keep it that way: when a number comes from real
data, name the data file, the script and the window.

## Rules

- Environment: `pixi install`, then `pixi run <task>` (tasks in
  `pyproject.toml`). The `modflow6` conda-forge package provides `mf6`.
  `requirements.txt` is kept for pip users and must list the same packages.
- Scripts run from their own directory and write outputs there. Keep that
  until the code moves to a `src/` package; update the pixi tasks and tests
  together if paths change.
- Raw data goes in `data/` (gitignored). Commit only derived CSVs under
  ~10 MB and figures.
- dv/v production runs use SeisMIC or NoisePy with configs taken from the
  package documentation, not invented parameters. `dvv_stretch.py` is for
  quick checks only.
- `analysis/phase_test.py`: the effective-n correction is deliberately
  conservative. Do not loosen it, or widen the tau range, to turn an
  AMBIGUOUS verdict into SUPPORTS.
- Hydrology inputs: Spirit Lake SNOTEL is windswept and rain-shadowed, so do
  not use it as a flank proxy. Lewis River mainstem gauges are dam-regulated;
  use headwater tributaries.
- Sign and unit conventions: dv/v as a fraction unless a column says `%`;
  head in metres; beta0 in 1/Pa. State the convention in every new CSV header
  or docstring.
- If a change alters a committed JSON result, regenerate it with the pixi task,
  commit the new JSON and figure together, and say in the commit message which
  numbers in `README.md` or `docs/` moved.

## Decision gates (from HANDOFF.md)

- After the MSH phase test (HANDOFF task 5): FAILS in all bands and both coda
  windows means stop the time-lapse branch, write a negative result, and pivot
  to static Vp/Vs at Santiam. SUPPORTS or AMBIGUOUS in 1–4 Hz means continue
  to tasks 6–8.
- After the 3-D MODFLOW calibration (task 8): recovered beta0 below
  ~1e-8 /Pa means a Santiam time-lapse deployment is not worth funding.
- The Santiam static transect is the existence test and does not depend on
  these gates.
