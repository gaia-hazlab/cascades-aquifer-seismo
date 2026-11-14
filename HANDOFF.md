# HANDOFF — next working session (Cowork)

Read `README.md`, then `docs/00_critique_and_reframe.md`. Raw data goes in `data/` (gitignored); commit only derived CSVs under ~10 MB plus figures.

## Trust levels

- **Verified here:**
  - `forward/*`, `modflow/*` (MODFLOW 6.7.0 ran to normal termination).
  - `analysis/phase_test.py` (self-test).
  - `pipeline/dvv_stretch.py` (synthetic test).
  - `pipeline/04_select_pairs.py` (smoke test).
- **Not verified against live services:**
  - `01_station_inventory.py` (ObsPy FDSN EARTHSCOPE + NCEDC).
  - `02_hydro_inventory.py` (`dataretrieval` 1.4 `waterdata` + `ngwmn`; request construction checked).
  - `03_snotel.py`: the NRCS report-generator URL pattern is the least certain item; check it first.
- **Priors, not facts:**
  - β₀ (one dynamic measurement).
  - The +15 % Vp gain on saturation.
  - Sy / fracture porosity.
  - The 2-D hillslope geometry.

## Tasks (in order)

| # | Task | Acceptance criterion |
|---|---|---|
| 1 | Run `01_station_inventory.py`. Fill station counts in docs/01 §2 | `coverage_summary.csv` committed; number of ≥10-yr stations in the msh, santiam_pass, three_sisters, and shasta boxes stated |
| 2 | Run `03_snotel.py`, fixing the URL if needed | `data/forcing_june_lake.csv` and `forcing_swift_creek.csv` with ≥15 water years; peak-SWE median printed and plausible (~1–2 m) |
| 3 | Run `04_select_pairs.py` on the real inventory | `pairs_msh.csv`; at least ~5 usable pairs in each of 1–2 and 2–4 Hz, otherwise relax the sector/crater rules and record why |
| 4 | Compute St. Helens dv/v in 4 bands (0.5–1, 1–2, 2–4, 4–8 Hz) with SeisMIC (Makus's setup) or NoisePy, south/west-flank pairs only, early vs late coda windows | `data/dvv_msh.csv` (date, band, dvv, err, window). Configs taken from the package docs, not invented |
| 5 | `analysis/phase_test.py` per band and window | `phase_test_results.json`; verdict table added to a new `docs/03_msh_results.md` |
| 6 | Pull REDPy St. Helens catalogs (surface + borehole) from assets.pnsn.org/red; doublet P and S dt by season on borehole stations | dVp/Vp and dVs/Vs seasonal amplitudes with errors; check B201–B204 depths in metadata |
| 7 | Hydroseismicity lag at St. Helens (Saar & Manga 2003 method): declustered PNSN rate vs June Lake melt | Lag and implied diffusivity with uncertainty |
| 8 | 3-D MODFLOW 6 south-flank model (FloPy); calibrate to headwater baseflow recession + task 7 diffusivity + task 5 τ | Joint posterior (or grid) on K-scale, Sy, β₀ |

## Decision gates

- **After task 5:**
  - Phase test FAILS in all bands and both coda windows → stop the time-lapse branch. Write it up as a negative result, then pivot fully to static Vp/Vs at Santiam.
  - SUPPORTS or AMBIGUOUS in 1–4 Hz → continue to tasks 6–8.
- **After task 8:**
  - Recovered β₀ < ~1×10⁻⁸ Pa⁻¹ → a Santiam time-lapse deployment is not worth funding. Do the static transect only.
- **Santiam static transect** (summer, 2–4 weeks of nodes across the old/young-rock boundary): independent of the gates above. This is the existence test.

## Cautions

- The `phase_test.py` effective-n correction is conservative when an aquifer signal is present (n_eff is computed from the null model's residuals). Do not loosen it to get a SUPPORTS verdict.
- Spirit Lake SNOTEL is windswept and rain-shadowed; don't use it as a flank proxy.
- Lewis River mainstem gauges are dam-regulated; use headwater tributaries.
- Keep St. Helens results framed as method calibration, not evidence for the Oregon aquifer.

## Open questions for Leif

- Water-table depth and its seasonal range at the crest. Any repeat temperature logs?
- Do resistivity, AEM, or MT data exist at Santiam (USGS co-authors)?
- Which springs are continuously gauged?
- Has he seen the "Goffrey" St. Helens attenuation paper? We need the DOI.
