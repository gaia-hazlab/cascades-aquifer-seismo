# 03. Live inventories (HANDOFF tasks 1–3)

Run on 2026-11-14 from branch `live-inventories` with the pixi environment
(ObsPy 1.5.1, dataretrieval 1.4.0). All three scripts ran unmodified.
`pipeline/02_hydro_inventory.py` (USGS + NGWMN) was not run in this session.

## Task 1. Station inventory

Command: `pixi run stations` (`pipeline/01_station_inventory.py`; FDSN
EARTHSCOPE + NCEDC, channels `HH?,BH?,EH?,HN?,DP?,GP?`, radius from
`pipeline/targets.py`). Output: `pipeline/stations_<target>.csv`,
`pipeline/coverage_summary.csv`.

| Target | Stations | 3-component | ≥5 yr | ≥10 yr | Median pair (km) |
|---|---|---|---|---|---|
| msh | 3699 | 430 | 36 | 26 | 21.3 |
| adams | 566 | 29 | 2 | 2 | 17.5 |
| indian_heaven | 1054 | 20 | 3 | 3 | 23.6 |
| santiam_pass | 135 | 129 | 8 | 5 | 20.8 |
| three_sisters | 236 | 234 | 12 | 9 | 20.4 |
| shasta | 72 | 67 | 21 | 13 | 22.6 |
| medicine_lake | 30 | 20 | 9 | 8 | 25.6 |
| lassen | 111 | 110 | 15 | 13 | 11.6 |

Caveats on these counts:

- "Years" is the span from a station's earliest channel start to its latest
  channel end in the metadata. It is an upper bound on continuous data: gaps,
  instrument swaps and strong-motion-only (`HN?`) epochs are all counted.
  Waveform availability has not been queried.
- The large station totals at msh, indian_heaven and adams are temporary
  dense deployments (in the msh box: XD 2378 stations, 1D 898, YI 136).
  The long-record count is what matters for dv/v.
- NCEDC returned no data for two of the eight targets (the script does not
  log which); the EARTHSCOPE query succeeded for all eight.

## Task 2. SNOTEL forcing

Command: `pixi run snotel` (`pipeline/03_snotel.py`). The NRCS
report-generator URL pattern worked as written; the returned column order
(SWE, accumulated precipitation, mean air temperature) matches what the script
assumes, checked on a 3-day request for station 553. Output:
`data/forcing_<site>.csv` (gitignored; regenerate with the command above).

| Site | Record | Water years | Median water-year peak SWE (m) | Missing SWE / precip / Tair |
|---|---|---|---|---|
| june_lake (553) | 1997-10-01 to 2026-09-30 | 29 | 1.23 | 0 % / 0 % / 1.6 % |
| swift_creek (1012) | 2002-08-13 to 2026-09-30 | 25 | 1.91 | 0.6 % / 1.2 % / 3.8 % |
| potato_hill (702) | 1997-10-01 to 2026-09-30 | not computed | 0.86 (calendar-year max) | not computed |
| surprise_lakes (804) | 1997-10-01 to 2026-09-30 | not computed | 1.27 (calendar-year max) | not computed |

Both St. Helens sites meet the acceptance criterion (≥15 water years, peak SWE
~1–2 m). The script's own printout groups by calendar year; the June Lake and
Swift Creek medians above were recomputed by water year and came out the same.

## Task 3. Pair selection

Command: `pixi run pairs` (`pipeline/04_select_pairs.py` on
`pipeline/stations_msh.csv`; S+W sector 135–315°, crater exclusion 3 km,
≥3 yr overlap). Output: `pipeline/pairs_msh.csv`: 15 stations, 74
inter-station pairs and 15 single-station entries.

| Band | Inter-station pairs | of which ≥10 yr overlap | Single-station |
|---|---|---|---|
| 0.5–1 Hz | 50 | not computed | 0 |
| 1–2 Hz | 21 | 7 | 15 |
| 2–4 Hz | 6 | 3 | 15 |
| 4–8 Hz | 3 | not computed | 15 |

The acceptance criterion (about 5 usable pairs in each of 1–2 and 2–4 Hz) is
met without relaxing the sector or crater rules. The 2–4 Hz inter-station set
is thin: CC.FLAT–PB.B203, CC.SWF2–CC.USFR, CC.SWF2–UW.SHW, CC.USFR–UW.SHW,
PB.B203–UW.FL2, PB.B204–UW.JUN. Overlap uses the same metadata span as task 1,
so it is an upper bound.

Stations selected: CC.FLAT, CC.SWF2, CC.UNFR, CC.USFR, PB.B203, PB.B204,
UW.ELK, UW.FL2, UW.FLT, UW.JUN, UW.LVP, UW.MTM, UW.SH2, UW.SHW, UW.TOUT.

## Before task 4

Query waveform availability for the 15 selected stations and recompute overlap
from real data spans before choosing dv/v pairs.
