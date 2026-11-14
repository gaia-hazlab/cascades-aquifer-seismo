# cascades-aquifer-seismo

Seismic tests of the Cascade crest volcanic aquifer (Karlstrom et al. 2025, PNAS) — Denolle Lab × Karlstrom (UO). Working draft, Nov 2026.

**Framing.** Time-lapse seismology cannot corroborate the *existence or volume* of the aquifer: it sees head changes, not storage, and the well-instrumented site (Mount St. Helens) is not where the aquifer was mapped. The project therefore asks two questions:

1. **Existence and extent** — static Vp/Vs and resistivity, validated at drill holes.
2. **Function** — time-lapse dv/v response time and band dependence, plus hydroseismicity, tested as an old-rock vs young-rock contrast across Santiam Pass.

Mount St. Helens is the method-calibration laboratory. See [`docs/00_critique_and_reframe.md`](docs/00_critique_and_reframe.md).

## Status

| Component | State |
|---|---|
| Forward model (Rayleigh dc/c from head, saturation, snow) | ✅ run, synthetic |
| Band design (kernel depths, attenuation vs distance) | ✅ run |
| MODFLOW 6 hillslope (Saar & Manga k(z)) → predicted multi-band dv/v | ✅ run (mf6 6.7.0) |
| Phase/lag falsification test | ✅ self-test passes: detects synthetic aquifer, rejects snow-only null |
| Stretching dv/v | ✅ synthetic test |
| Station / hydro / SNOTEL inventories, pair selection | ⚠️ written; **not run against live services** (sandbox had no FDSN/USGS/NRCS access); pair selection smoke-tested on fake stations |
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
HANDOFF.md  task list and acceptance criteria for the next working session
```

## Run order (St. Helens calibration)

```bash
pip install -r requirements.txt          # + mf6 on PATH for modflow/
cd pipeline
python 01_station_inventory.py           # stations_*.csv, coverage_summary.csv
python 04_select_pairs.py                # pairs_msh.csv (S/W flanks, band rules)
python 02_hydro_inventory.py             # USGS + NGWMN wells/streams
python 03_snotel.py                      # ../data/forcing_*.csv  (verify URL first run)
# compute dv/v in 0.5-1, 1-2, 2-4, 4-8 Hz with SeisMIC or NoisePy -> data/dvv_msh.csv
cd ../analysis
python phase_test.py --dvv ../data/dvv_msh.csv --forcing ../data/forcing_june_lake.csv

# synthetic predictions (regenerates modflow/mf6_ws/, which is gitignored)
cd ../modflow && python hillslope_mf6.py && python couple_dvv.py
```

## Key numbers (synthetic; see docs for assumptions)

- **β₀ ≈ 2.5×10⁻⁸ Pa⁻¹**, from 0.006 MPa⁻¹ at ~1 km (Taira & Brenguier 2016, Lassen). This is a dynamic value, so treat it as an upper bound.
- **Seasonal water-table swing (MODFLOW, Sy 0.02–0.1):** 8–21 m upslope, 3–12 m mid/lower slope.
- **Predicted seasonal dv/v:** 0.03–0.1 % peak-to-peak where the water table is ≲100 m deep; below noise where it is ~260 m deep. The signature is the ~12-week lag between the snow-driven maximum and the head-driven minimum.
- **Primary band 1–2 Hz** (Vs-kernel median ~0.5 km in young lava). Anchor with 2–4 Hz (~0.17 km) and 0.5–1 Hz (~1.1 km). Above ~4 Hz, use only pairs closer than ~3 km.

## Related

GAIA digital twin: `couple_dvv.py` is a prototype of the head → dv/v observation operator; `phase_test.py` is its simplest inverse.
