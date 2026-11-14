"""Head(t) from hillslope_mf6.py -> predicted dv/v(t) per frequency band.
Linearised operator: dc/c(t) = G_head(z_wt) * dh(t) + G_snow * SWE(t), with
G from finite differences of forward_dvv.perturb at the site's mean water-table
depth. beta0 = 2.5e-8 /Pa, calibrated so beta(~1 km) matches the 0.006 /MPa
susceptibility of Taira & Brenguier (2016) at Lassen (dynamic -> upper bound).
"""
import json, sys
import numpy as np
sys.path.insert(0, "../forward")
import forward_dvv as fw
from hillslope_mf6 import TOP, DX, recharge_series

BETA0, PHI = 2.5e-8, 0.05
BANDS = {"4-8 Hz": 1 / np.sqrt(32), "2-4 Hz": 1 / np.sqrt(8), "1-2 Hz": 1 / np.sqrt(2),
         "0.5-1 Hz": 1 / np.sqrt(0.5)}   # ascending period (disba requirement)
fw.PERIODS = np.array(list(BANDS.values()))
m, zmid = fw.build_model(); c0 = fw.phase_c(m)

wt = np.load("mf6_ws/wt_sy05.npy")[-52 * 3:]        # last 3 periodic years, weekly
weeks = np.arange(len(wt))
woy = weeks % 52
# SWE (m): accumulates weeks 44->13 (Nov->Apr 1) to 1.0 m, melts weeks 13->26
swe = np.where(woy < 13, (woy + 9) / 22, np.where(woy < 26, 1 - (woy - 13) / 13,
               np.where(woy >= 44, (woy - 44) / 22, 0.0)))

out = {}
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, axs = plt.subplots(2, 3, figsize=(13, 6), sharex=True)
for col, xkm in enumerate([1, 3, 5]):
    j = int(xkm * 1000 // DX)
    wtj = np.minimum(wt[:, j], TOP[j])
    zwt = float(TOP[j] - wtj.mean()) / 1000
    dh = wtj - wtj.mean()
    gh = fw.dcc(m, fw.perturb(m, zmid, z_wt=zwt, dh=1.0, beta0=BETA0, phi=PHI), c0)
    gs = fw.dcc(m, fw.perturb(m, zmid, z_wt=zwt, swe=1.0, beta0=BETA0), c0)
    pred = {b: 100 * (gh[i] * dh + gs[i] * swe) for i, b in enumerate(BANDS)}
    out[f"x{xkm}km"] = dict(mean_wt_depth_m=round(zwt * 1000, 1), head_range_m=round(float(np.ptp(dh)), 2),
                            head_only_pct_per_m={b: round(100 * float(gh[i]), 4) for i, b in enumerate(BANDS)},
                            snow_pct_per_m_swe={b: round(100 * float(gs[i]), 4) for i, b in enumerate(BANDS)},
                            peak_to_peak_total_pct={b: round(float(np.ptp(pred[b])), 3) for b in BANDS},
                            peak_week_of_year={b: int(woy[np.argmax(pred[b][-52:])]) for b in BANDS})
    axs[0, col].plot(weeks / 52, dh, "k"); axs[0, col].set_title(f"x = {xkm} km, WT depth {zwt*1000:.0f} m")
    axs[0, col].set_ylabel("head anomaly (m)") if col == 0 else None
    ax2 = axs[0, col].twinx(); ax2.fill_between(weeks / 52, swe, color="tab:cyan", alpha=0.2)
    for b in BANDS:
        axs[1, col].plot(weeks / 52, pred[b], label=b)
    axs[1, col].axhspan(-0.03, 0.03, color="gray", alpha=0.2)
    axs[1, col].set_xlabel("years")
axs[1, 0].set_ylabel("predicted dc/c (%)"); axs[1, 0].legend(fontsize=7)
fig.suptitle("MODFLOW 6 heads (Sy=0.05) -> Rayleigh dc/c, beta0=2.5e-8/Pa, SWE 1 m (cyan); grey = ±1.5σ noise")
fig.tight_layout(); fig.savefig("coupled_dvv.png", dpi=140)
json.dump(out, open("coupled_dvv.json", "w"), indent=1)
print(json.dumps(out, indent=1))
