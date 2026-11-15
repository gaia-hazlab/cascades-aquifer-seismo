# cascades-aquifer-seismo

Seismic tests of the Cascade crest volcanic aquifer (Karlstrom et al. 2025, PNAS) — Denolle Lab × Karlstrom (UO). Working draft, Nov 2026.

**Framing.** Time-lapse seismology cannot corroborate the *existence or volume* of the aquifer: it sees head changes, not storage, and the well-instrumented site (Mount St. Helens) is not where the aquifer was mapped. The project therefore asks two questions:

1. **Existence and extent** — static Vp/Vs and resistivity, validated at drill holes.
2. **Function** — time-lapse dv/v response time and band dependence, plus hydroseismicity, tested as an old-rock vs young-rock contrast across Santiam Pass.

Mount St. Helens is the method-calibration laboratory. See [`docs/00_critique_and_reframe.md`](docs/00_critique_and_reframe.md).

**Direction (Nov 2026).** The project is moving from a single seismic test to joint assimilation of all available data (discharge, wells, drill-hole temperatures, GNSS, SNOTEL, dv/v, attenuation) into a groundwater model, to identify or not and characterise the reservoir, following the GAIA Mount Rainier approach. See [`docs/05_assimilation_design.md`](docs/05_assimilation_design.md) (draft).

## Status

| Component | State |
|---|---|
| Forward model (Rayleigh dc/c from head, saturation, snow) | ✅ run, synthetic |
| Band design (kernel depths, attenuation vs distance) | ✅ run |
| MODFLOW 6 hillslope (Saar & Manga k(z)) → predicted multi-band dv/v | ✅ run (mf6 6.7.0) |
| Phase/lag falsification test | ✅ self-test passes: detects synthetic aquifer, rejects snow-only null |
| Stretching dv/v | ✅ synthetic test |
| Station inventory, SNOTEL forcing, pair selection | ✅ run against live services 2026-11-14, see [`docs/03_live_inventories.md`](docs/03_live_inventories.md) |
| Hydro inventory (USGS discharge, wells, springs), SNOTEL and GNSS station lists | ✅ run against live services 2026-11-15; NGWMN returned nothing; counts in [`docs/05_assimilation_design.md`](docs/05_assimilation_design.md) §4 |
| Assimilation framework (R versus S model classes, ensemble smoother) | ❌ design draft only |
| Real St. Helens dv/v, repeaters, Santiam data | ❌ not started |

Every number in the docs is a literature value or a synthetic result unless cited.

## Layout

```
docs/
  00_critique_and_reframe.md   <- start here
  01_feasibility.md            desk study, target sites, forward model, first plan
  02_interstation_dvv_bands_repeaters_hydro.md
                               bands, inter-station strategy, repeaters, MSH–Adams
                               hydrology inventory, MODFLOW coupling
pipeline/   targets.py, 01_station_inventory.py, 02_hydro_inventory.py (USGS + NGWMN),
            03_snotel.py, 04_select_pairs.py, dvv_stretch.py
forward/    forward_dvv.py, band_design.py, separability.py (+ results, figures)
modflow/    hillslope_mf6.py, couple_dvv.py (+ results, figure)
analysis/   phase_test.py   <- the falsification test
tests/      regression tests for the synthetic results (pixi run test)
HANDOFF.md  task list and acceptance criteria for the next working session
AGENTS.md   rules for coding agents and contributors
```

## Setup

```bash
pixi install          # conda-forge env incl. modflow6 (mf6 on PATH), obspy, flopy; disba + dataretrieval from PyPI
pixi run test         # synthetic regression: forward, band design, MODFLOW 6 hillslope + coupling, phase test, stretching
```

`requirements.txt` is kept for pip users (then install `mf6` from MODFLOW-ORG/executables yourself).

## Run order (St. Helens calibration)

```bash
pixi run stations     # pipeline/01: stations_*.csv, coverage_summary.csv
pixi run pairs        # pipeline/04: pairs_msh.csv (S/W flanks, band rules)
pixi run hydro        # pipeline/02: USGS + NGWMN wells/streams
pixi run snotel       # pipeline/03: data/forcing_*.csv (verify URL first run)
# compute dv/v in 0.5-1, 1-2, 2-4, 4-8 Hz with SeisMIC or NoisePy -> data/dvv_msh.csv
cd analysis && pixi run python phase_test.py --dvv ../data/dvv_msh.csv --forcing ../data/forcing_june_lake.csv
```

Synthetic predictions: `pixi run forward`, `pixi run band-design`, `pixi run separability`, `pixi run couple` (runs `hillslope` first; regenerates `modflow/mf6_ws/`, which is gitignored).

## Key numbers (synthetic; see docs for assumptions)

- **β₀ ≈ 2.5×10⁻⁸ Pa⁻¹**, from 0.006 MPa⁻¹ at ~1 km (Taira & Brenguier 2016, Lassen). This is a dynamic value, so treat it as an upper bound.
- **Seasonal water-table swing (MODFLOW, Sy 0.02–0.1):** 8–21 m upslope, 3–12 m mid/lower slope.
- **Predicted seasonal dv/v:** 0.03–0.1 % peak-to-peak where the water table is ≲100 m deep; below noise where it is ~260 m deep. The signature is the ~12-week lag between the snow-driven maximum and the head-driven minimum.
- **Primary band 1–2 Hz** (Vs-kernel median ~0.5 km in young lava). Anchor with 2–4 Hz (~0.17 km) and 0.5–1 Hz (~1.1 km). Above ~4 Hz, use only pairs closer than ~3 km.

## Related

GAIA digital twin: `couple_dvv.py` is a prototype of the head → dv/v observation operator; `phase_test.py` is its simplest inverse.
