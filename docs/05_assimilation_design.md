# 05. Assimilation design: identify (or not) and characterise the Cascade crest reservoir

Draft, 2026-11-15. Supersedes the single-test framing of `HANDOFF.md` as the
project's organising idea; the phase test stays as a diagnostic (section 7).
Nothing here is implemented yet except where a script is named.

## 1. Question

Karlstrom et al. (2025, PNAS) infer at least 81 km³ of actively circulating
water under the central Oregon Cascade crest from drill-hole temperature
profiles. The question is whether every other observation we can obtain is
consistent with a reservoir of that depth and volume, and if so what its
thickness, permeability structure and storage properties are. The approach
follows the Mount Rainier work in GAIA: stage all data for the site, own the
hydrological state in one model, attach one observation operator per data
type, and let the data constrain state and parameters jointly.

## 2. Hypotheses as model classes

| Class | Description | Distinguishing prediction |
|---|---|---|
| R (reservoir) | Permeable young volcanics to 1 km or more below the crest; deep water table; long flow paths | Isothermal upper section in drill holes; large stable spring discharge with long recession; head response lagged and damped at depth; mass change larger than shallow storage can hold |
| S (shallow only) | Active flow confined to the upper few hundred metres over low-permeability rock | Conductive temperature gradient from shallow depth; flashier baseflow; seasonal head response in phase at all depths sampled |

"Identify or not" is a comparison of R and S on the same data, with held-out
observations (section 6). "Characterise" is the posterior of R's parameters.

## 3. State, parameters, forcing

- **State** (owned by the groundwater model): head h(x, z, t), water-table
  elevation, storage change, spring and seepage discharge. Temperature
  T(x, z) if heat transport is included.
- **Parameters**: permeability k(z) (Saar and Manga 2004 form as prior:
  surface value, decay length, depth of the low-permeability floor),
  anisotropy, specific yield Sy, specific storage Ss, recharge fraction of
  precipitation, basal heat flux. For the seismic operators: stress
  sensitivity beta0 and its depth decay, saturation effect on Vp.
- **Forcing**: daily snow water equivalent, precipitation and temperature
  from SNOTEL, distributed with a gridded product (PRISM; `prism-stac` exists
  in gaia-hazlab).
- **Model**: MODFLOW 6 through FloPy. Start from `modflow/hillslope_mf6.py`
  (2-D section, verified) as a crest-to-valley transect through the McKenzie
  headwaters, then 3-D. Heat: MODFLOW 6 GWE (energy transport) is the
  candidate; it has not been tested here.

## 4. Observations and operators

Counts are from the inventories run on 2026-11-14/15
(`pipeline/coverage_summary.csv`, `hydro_summary.csv`,
`obs_inventory_summary.csv`); boxes are ±0.30° around the target centre
(`pipeline/targets.py`).

| Observation | Operator (model to data) | Constrains | Santiam Pass box | Three Sisters box | Status |
|---|---|---|---|---|---|
| Drill-hole temperature profiles | T(z) at the hole from coupled flow and heat | Circulation depth, recharge, k(z) | not inventoried | not inventoried | Data with Leif. This is the primary evidence and has no substitute |
| Stream discharge, daily | Simulated drain and river flux at the gauge | Storage, k, recharge | 18 gauges; 6 active with ≥20 yr | 15; 3 active with ≥20 yr | Downloaded (`discharge_*.parquet`, gitignored) |
| Spring discharge | Drain flux at the spring | Deep flow paths | 36 spring sites, none with daily discharge in NWIS | 34, none | Gap. Ask Leif and Oregon Water Resources Department |
| Well water levels | h at screen depth | Head, Sy | 32 wells; 5 with ≥10 measurements; 1 active | 111; 12 with ≥10; 1 active | Downloaded. Sparse in time; mostly east flank |
| SNOTEL | Forcing | Recharge | 9 sites, most from 1978–79 | 6 | Station list done; `03_snotel.py` needs the Oregon IDs |
| GNSS vertical | Elastic load response to modelled water mass change | Total storage change | 8 stations, 8 with ≥10 yr, 2 active in 2026 | 16; 10 with ≥10 yr; 6 active | Station list done; series not downloaded |
| dv/v by band | Head and saturation to Rayleigh dc/c (`forward/forward_dvv.py`, `modflow/couple_dvv.py`) | Head change with depth, beta0 | 5 seismic stations with ≥10 yr metadata span | 9 | Operator verified on synthetics; no data |
| Seismic attenuation ratio (DSAR, Köpfli et al. 2024) | Saturation to attenuation; no operator yet | Shallow saturation timing | same stations | same stations | Method published; operator not written |
| Seasonal seismicity | Pore-pressure diffusion to rate change (Saar and Manga 2003) | Hydraulic diffusivity | not inventoried | not inventoried | Not started |
| Resistivity, magnetotellurics | Archie-type saturation to resistivity | Static extent | unknown | unknown | Open question for Leif |
| Static Vp/Vs | Saturation and porosity to velocity | Static extent | no dense array | no dense array | Would need the proposed nodal transect |

Known contaminants to model or mask:

- **Three Sisters uplift.** Volcanic inflation west of South Sister has been
  documented in the literature since the late 1990s (not re-verified in this
  session). It affects GNSS vertical and possibly dv/v, so the GNSS operator
  needs a volcanic deformation term or the affected stations left out.
- **Regulated flow.** Two of the long McKenzie gauges are below dams or
  reservoirs (USGS-14158850 below Trail Bridge Dam, USGS-14158790 above
  Smith River Reservoir). USGS-14158500, McKenzie River at the outlet of
  Clear Lake (1912 to present), is spring-fed headwater and the most useful
  single discharge record.
- **Well bias.** The three longest well records (USGS-442242121405501,
  -441550121314701, -441732121300501) are east of the crest at 195–403 ft
  depth. Well positions relative to the crest have not been mapped for the
  rest.
- NGWMN (state-agency wells) returned nothing through `02_hydro_inventory.py`;
  whether that is a real absence or a failed request is not established.
  Oregon Water Resources Department wells are not covered by the script.

## 5. Method

1. **Stage** every data type as typed, versioned arrays with provenance, as
   `gaia-peters-dome` does with `gaia-cli`. Raw data stays out of git.
2. **Prior ensemble** of R and S models (a few hundred members each) from the
   parameter priors in section 3.
3. **Assimilate** with an iterative ensemble smoother over the full record:
   parameters and state updated together, all observation types at once, each
   with its own error model. PEST++ IES through `pyemu` is the proposed tool,
   because it is built for MODFLOW 6 and `hydrostate` already carries a
   `pyemu` extra. A sequential filter is not needed for a retrospective
   characterisation.
4. **Observation errors** include operator error, not just instrument noise.
   For dv/v this is large: beta0 is known from one dynamic measurement.
   Treat beta0 as a parameter with a wide prior, informed by St. Helens
   (section 7).
5. **Order of assimilation for diagnosis**: discharge and wells first, then
   add temperature profiles, then GNSS, then seismic. Record how much each
   addition narrows the posterior of reservoir thickness and Sy. That table is
   the answer to "what does seismology add".

## 6. How "identify or not" is decided

- Fit R and S to the same training data; compare on held-out data: withheld
  gauges, withheld water years (dry 2015 and wet 2017 are natural tests), and
  one whole data type withheld in turn.
- Report posterior predictive skill for each class and each data type, plus
  the posterior of the depth of the permeability floor in R. If that
  posterior piles up at shallow depth, R has collapsed onto S and the
  reservoir is not identified.
- State in advance what would count against R: temperature profiles fitted
  equally well by S with plausible heat flux; storage change from GNSS no
  larger than S can hold; no depth-dependent lag in head-sensitive data.
- Volume follows from thickness, extent and porosity. Seismology and GNSS
  constrain head and mass change, not porosity directly, so the volume
  estimate will stay tied to the temperature profiles and to drill-hole
  porosity. Say so in every product.

## 7. Role of Mount St. Helens

St. Helens has the long seismic record (26 stations with ≥10 yr metadata
span, 30 GNSS stations, 9 SNOTEL sites, a borehole water-level record after
2020) but is not where the reservoir was mapped. Its job is to calibrate the
seismic operators: estimate beta0 and the snow-load term where the forcing
and head are best known, then carry that posterior to Oregon as a prior. The
phase test (`analysis/phase_test.py`) becomes a check on the operator, and
the constraints in `docs/04_prior_msh_dvv.md` apply.

## 8. Relation to other GAIA code

| Need | Existing | Decision pending |
|---|---|---|
| Groundwater state | `hydrostate` (MODFLOW 6 template, sensor operators, DataHub interchange) | Build on it, or keep a standalone FloPy model here until the transect works |
| Seismic operators | `mechanicalstate` (retention, effective stress, elastic response) versus `forward/forward_dvv.py` here | Which petrophysics is the reference; they have not been compared |
| Data staging | `gaia-cli`, pattern of `gaia-peters-dome` | Whether this repo is the data container or a second repo is |
| Forcing | `prism-stac`, `usgs-gauge-utils` | Reuse `usgs-gauge-utils` in place of `02_hydro_inventory.py`? Not checked |

Recommendation: standalone 2-D transect first, with interfaces shaped like
`hydrostate`'s so the move is cheap, and adopt `gaia-cli` staging from the
start.

## 9. First steps

1. Get from Leif: temperature profiles (locations, depths, dates), drill-hole
   porosity and lithology, any spring gauging, any resistivity or
   magnetotelluric data.
2. Pick the transect (crest to Clear Lake and the McKenzie) and stage
   discharge, wells, SNOTEL and GNSS for it.
3. Extend the hillslope model to that transect with real topography; build
   the R and S prior ensembles; check prior predictive discharge against
   USGS-14158500.
4. Add the heat-transport operator and test it on a published profile.
5. In parallel at St. Helens: beta0 calibration per `docs/04`.

## 10. Open questions

- Which drill holes, and can the profiles be shared and versioned in a public
  repository?
- Is a 2-D transect defensible given along-arc flow?
- Is the 81 km³ figure tied to a porosity we can test independently?
- Does anyone gauge Olallie or Great Springs continuously?
