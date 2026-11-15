# 04. Prior St. Helens work and what it changes for HANDOFF task 4

Written 2026-11-15. Both papers were read in full text plus supplement from
the GFZpublic PDFs (text extraction; figures were not read, so no amplitude
below comes from a plot). Statements marked "checked" were re-found in the
extracted text in this session; the rest are from the reading pass only.

## The two papers

| | Makus et al. 2024 | Köpfli et al. 2024 |
|---|---|---|
| Journal | Seismological Research Letters 95(5), 2674–2688, doi:10.1785/0220240088 | Seismological Research Letters 95(5), 2622–2636, doi:10.1785/0220240079 (Crossref, checked; not Seismica) |
| Observable | dv/v, SeisMIC 0.5.22, stretching | No dv/v. RSAM, DSAR (displacement seismic amplitude ratio, 4.5–8 over 8–16 Hz), spectral width, scattering network |
| Period | 1998–2023 | 2000–2022 |
| Bands | 0.25–0.5, 0.5–1, 1–2 Hz. Data decimated to 5 Hz | 2–5, 4.5–8, 8–16 Hz amplitudes |
| Code | github.com/Denolle-Lab/Mt-St-Helens (no licence, no DOI) | github.com/koepflma/MSH_AmbientSeismicWavefield (MIT) |
| Archived products | None found: no dv/v series or correlation functions | None found: no DSAR or RSAM series |

## What Makus et al. established

- Processing: 1 h windows, one-bit, whitening, 5-day stacks, 60-day smoothing,
  one coda window per band from 4 to 50 low-cut periods (8–108 s at 0.5–1 Hz,
  4–54 s at 1–2 Hz). No early-versus-late coda split.
- **Autocorrelations of analog-telemetry single-component stations were
  discarded** because of a comb-like artifact at about 13 s (checked).
- **Clock step of 0.25 s on all analog stations** after a PNSN digitizer
  restart. The supplement and one main-text passage date it 17 October 2013;
  another main-text passage says October 2011 (checked: both dates appear).
  They split each affected series in two at the step.
- Daily QC with MUSTANG `max_range` under 500 counts and RMS over 300 times
  the channel median.
- Seasonal cycle at 0.5–2 Hz has two peaks (March and September) in the
  network median; phase depends on location. On the edifice: snow load and
  freezing. Away from it: pore-space saturation plus thermoelastic stress,
  with snow load and freezing having "limited impacts" (checked).
- The autumn peak is attributed to lower pore pressure or a 70 to 80 day
  phase-shifted thermoelastic effect, likely both (checked).
- Seasonal amplitude per band is not given as a number. No hydrological
  model, fitted lag or diffusivity.
- Non-hydrological steps: Nisqually 2001 (0.05 to 0.2 % drop, slow recovery),
  2004 eruption onset (0.1 to 0.2 % rise), 2017–2020 (about 0.2 % rise).
- Forcing used for visual comparison: Swift Creek SNOTEL, ERA5 rain plus
  modelled melt, Spirit Lake level, a borehole level record after 2020.

## What Köpfli et al. established

- DSAR has a seasonal cycle over 22 years that the authors read as
  structural (attenuation), not source-driven.
- Network-stacked DSAR and borehole water level are offset by 3 months
  (checked). At UW.SHW, the one southwest-flank station shown, DSAR is
  "almost aligned" with the borehole level (checked, Fig. S22 caption). The
  authors suggest the offset reflects measurement location.
- Stated limitation: snow height and borehole level peak together, so snow
  load and infiltration are hard to separate (from the reading pass; the exact
  sentence was not re-found).

## Consequences for this project

| Plan item (HANDOFF, docs/02) | Status after reading | Change |
|---|---|---|
| 0.5–1 and 1–2 Hz dv/v | Already computed by Makus et al. with QC and clock handling, but not archived | Ask Peter Makus for the SeisMIC correlation and dv/v files before recomputing |
| 2–4 and 4–8 Hz dv/v | Never computed (5 Hz decimation) | Fresh correlations from raw data; this is the new contribution |
| Single-station entries above 2 Hz on UW verticals | Autocorrelations of analog stations are artifact-ridden; these stations are vertical-only (docs/03) | Drop them. Single-station work only at CC broadband and PB borehole sites |
| Long records from 1998 | Analog clock step in October 2013; Nisqually and eruption steps | Split series at the clock step; mask or model 2001, 2004–2008 and 2017–2020 |
| South and west flank restriction | UW.SHW shows almost no DSAR-to-borehole offset; the 3-month offset is on the north side | The sector chosen to avoid the debris avalanche is where prior evidence for a lag is weakest. Run north-side pairs as a contrast, not only S/W |
| Phase test: SWE + head + temperature | A 70 to 80 day thermoelastic lag is close to the 12-week head lag; snow and borehole level peak together | Mean seasonal phase cannot separate them. `phase_test.py` needs interannual variability to do the work; check that its bootstrap over water years has power with about 20 years |
| Early versus late coda | Not done before | Still new |
| Forcing | Same Swift Creek SNOTEL; Spirit Lake level and borehole level are in the Denolle-Lab/Mt-St-Helens repo under `climate data/` | Reuse those files; a borehole head record is a direct regressor the plan did not have |

Combined with the availability check in docs/03: after dropping UW.FLT,
UW.SH2 and the vertical-only autocorrelations, the 2–4 Hz S/W-flank test
rests on two or three inter-station pairs plus single-station correlations at
PB.B203, PB.B204 and the CC broadbands (CC.SWF2 from 2013, the others from
2021 or later).

Not read here: Hotovec-Ellis et al. (2014, 2015), the earthquake-coda
velocity work at 1–10 Hz, which is the only prior result above 2 Hz.
