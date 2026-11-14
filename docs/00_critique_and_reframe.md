# 00 — Critique and reframe: can time-lapse seismology corroborate the Cascade crest aquifer?

**Short answer: not as originally framed.** Time-lapse seismology is a weak tool for corroborating the *existence or volume* of the Karlstrom et al. (2025) aquifer. It is a strong candidate for testing *how the aquifer works*: its response time, diffusivity, and the depth of seasonal circulation. Existence and extent should be tested with static imaging (Vp/Vs, resistivity) validated at the drill holes. This document explains why and restates the project as two questions with two toolsets.

## The claim being tested

Karlstrom et al. (2025, PNAS) infer from drill-hole temperature profiles that ≥81 km³ of active groundwater is stored at the Oregon Cascade crest (Santiam Pass / McKenzie headwaters). Water circulates through the upper ~1 km of young volcanic rock. The young-rock landscape has high vertical hydraulic conductivity, abundant lakes, and *muted hydrographs*. Older rock to the west has shallow flow and flashy hydrographs.

## Three problems with "time-lapse corroborates the aquifer"

1. **The data are in the wrong place.**
   - The long continuous records (25 yr dv/v; Makus et al. 2024), borehole stations, and live repeating-earthquake catalogs (PNSN REDPy) are at Mount St. Helens. That is a different volcano and a different hydrogeologic system, partly a 1980 debris avalanche.
   - The Santiam crest has sparse stations and essentially no repeaters.
   - St. Helens can therefore calibrate the method but cannot corroborate Leif's aquifer.
2. **Time-lapse sees change in head, not storage.**
   - dv/v responds to ∂h/∂t, snow load, and temperature. A large, well-buffered aquifer with muted hydrographs is close to the worst case for time-lapse detection.
   - In our MODFLOW 6 hillslope (Saar & Manga k(z), Sy = 0.05), the upslope column has a ~260 m deep water table. Its predicted seasonal dv/v is below an optimistic 0.02 % noise floor in every band.
   - A null result there would not falsify the aquifer. That asymmetry (positive results ambiguous, negative results uninformative) is the core weakness of the original framing.
3. **Non-uniqueness.**
   - Snow loading, thermoelastic strain, freeze–thaw, and seasonal noise-source changes all produce annual dv/v.
   - The phase test (snow-driven peak around 1 Apr; head-driven trough ~12 weeks later; `analysis/phase_test.py`) mitigates this but needs local forcing data and multi-year records.
   - The physics also rests on weak priors:
     - β₀ comes from one dynamic-stress measurement at a pressurized hydrothermal system (Taira & Brenguier 2016), so it is an upper bound for quasi-static loading.
     - The +15 % Vp gain on fracture saturation is essentially a guess.
     - The models are 1-D seismic and 2-D hydrologic.

## Reframe: two questions, two toolsets

| | Q1: Existence and extent | Q2: Function |
|---|---|---|
| Question | Is there saturated fractured rock to ~1 km at the crest, and where does it end? | How fast does the system respond, and how deep does the seasonal pulse penetrate? Is vertical K high, as Karlstrom infers? |
| Tool | **Static:** joint Rayleigh dispersion + H/V ellipticity for Vp/Vs (node array); resistivity, AEM, or MT; local-earthquake Vp/Vs where seismicity exists | **Time-lapse:** multi-band dv/v lag/τ (`phase_test.py`); hydroseismicity lag (Saar & Manga 2003 method); repeater dVp/Vp vs dVs/Vs at St. Helens |
| Ground truth | Drill-hole isothermal depths (Karlstrom 2025); well logs | Spring discharge and baseflow recession; SNOTEL melt timing; MODFLOW-predicted τ |
| Where | Santiam Pass old/young-rock transect | St. Helens (calibration), then Santiam (science, needs ≥3–5 yr deployment) |

**The sharpest test is the old-rock / young-rock contrast across Santiam Pass.** Same climate, different bedrock age, so Karlstrom's model makes opposite predictions:

| Observable | Young rock (crest) | Old rock (western Cascades) |
|---|---|---|
| Vp/Vs, 0.2–1 km | Elevated (saturated fractures) over a deep low-H/V zone | Normal; saturation confined to the top meters to tens of meters |
| dv/v response time τ | Long. Recharge diffuses deep, the head pulse arrives at depth late, and amplitude is muted | Short and flashy, tracking storms |
| Band dependence of seasonal dv/v | Signal reaches 0.5–1 Hz (z ~1 km) | Signal confined to 2–8 Hz (z < 0.25 km) |
| Hydroseismicity / diffusivity | High vertical diffusivity | Low vertical diffusivity |

A contrast in the predicted direction is corroboration that does not depend on knowing β₀. An absent or reversed contrast is a genuine test failure. This replaces "detect the aquifer" with "detect the state shift", which is the actual claim of the PNAS paper.

## Site roles

- **Mount St. Helens: method laboratory.** Calibrate β₀, the band structure, and the phase test against 25 years of data, the borehole stations, and repeaters. Do not present St. Helens results as evidence for the Oregon aquifer.
- **Santiam Pass: science target.**
  - Phase 1: static node transect plus H/V (2–4 weeks in summer), validated at drill holes. Pair with resistivity if any exists (ask Leif and USGS co-authors).
  - Phase 2: only if Phase 1 shows the contrast, a 3–5 yr broadband deployment across the transect for τ and band dependence.
- **Shasta–Medicine Lake–Lassen: secondary.** Lassen already has a dv/v record (Taira & Brenguier 2016) and NCSN stations. Fall River springs provide the best discharge record. Deep water tables make dv/v the hardest to detect here.

## What would convince a skeptic, and what would kill it

**Convincing:**
- Elevated Vp/Vs and low H/V on young rock that terminates at the age boundary and matches drill-hole circulation depths.
- At St. Helens, the phase test SUPPORTS in 1–4 Hz with τ in 20–200 days on south/west-flank pairs.
- At Santiam, the band dependence and τ differ across the age boundary in the predicted direction.

**Killing:**
- No Vp/Vs contrast across the age boundary at a resolution adequate for 0.2–1 km depth.
- St. Helens phase test FAILS across all bands and multi-year windows. Then dv/v is not hydrologically interpretable even at the best-instrumented site.
- τ indistinguishable across the boundary.

## What we have not done

No real waveforms have been processed. All numbers in this repository are literature values or synthetics. The verdicts above are the *design* of the test, not its result.
