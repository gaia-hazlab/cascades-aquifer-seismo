"""Frequency-band design for inter-station dv/v in young Cascade lavas.
(1) per band: Rayleigh phase velocity, wavelength, depth of peak Vs kernel,
    attenuation amplitude factor exp(-pi f r /(Q c)) vs inter-station distance
    (Q=30: crater-like Qp, Tusa et al. 2004; Q=100: flank prior).
(2) the sign-flip diagnostic: with beta0 calibrated from Taira & Brenguier
    (2016) (0.006/MPa at ~1 km  ->  beta0 ~ 2.5e-8 /Pa with sigma_c=10 MPa),
    the period at which dc/c changes sign tracks water-table depth.
"""
import json, numpy as np
from disba import PhaseDispersion, PhaseSensitivity
import forward_dvv as fw

m, zmid = fw.build_model()
BANDS = [(0.25, 0.5), (0.5, 1), (1, 2), (2, 4), (4, 8)]
DIST = [2, 5, 10, 20]
out = {"bands": []}
pd_ = PhaseDispersion(*m.T, dc=0.0001)
ps = PhaseSensitivity(*m.T)
for f1, f2 in BANDS:
    fc = np.sqrt(f1 * f2); T = 1 / fc
    c = float(pd_(np.array([T]), mode=0, wave="rayleigh").velocity[0])
    k = ps(T, mode=0, wave="rayleigh", parameter="velocity_s").kernel / m[:, 0]
    zpk = float(zmid[np.argmax(np.abs(k))])
    cum = np.cumsum(np.abs(k) * m[:, 0]); z90 = float(zmid[np.searchsorted(cum, 0.9 * cum[-1])])
    att = {f"Q{Q}": {f"{r}km": round(float(np.exp(-np.pi * fc * r / (Q * c))), 3) for r in DIST} for Q in (30, 100)}
    out["bands"].append(dict(band_hz=[f1, f2], fc=round(fc, 2), c_kms=round(c, 2),
                             wavelength_km=round(c / fc, 2), peak_depth_km=zpk,
                             depth_90pct_km=z90, min_pair_km_2lambda=round(2 * c / fc, 1), amp=att))
# (2) sign flip vs water-table depth
beta0 = 2.5e-8
P = fw.PERIODS; c0 = fw.phase_c(m)
flip = []
for zwt in [0.02, 0.05, 0.1, 0.2, 0.3, 0.5]:
    d = 100 * fw.dcc(m, fw.perturb(m, zmid, z_wt=zwt, dh=10.0, beta0=beta0), c0)
    s = np.sign(d); idx = np.where(np.diff(s) != 0)[0]
    flip.append(dict(z_wt_m=int(zwt * 1000), dcc_pct=dict(zip(P.tolist(), d.round(3).tolist())),
                     sign_flip_period_s=[round(float(np.sqrt(P[i] * P[i + 1])), 2) for i in idx]))
out["sign_flip_beta0_2.5e-8_dh10m"] = flip
json.dump(out, open("band_design.json", "w"), indent=1)
for b in out["bands"]:
    print(b["band_hz"], "c", b["c_kms"], "λ", b["wavelength_km"], "peak", b["peak_depth_km"],
          "z90", b["depth_90pct_km"], "minpair", b["min_pair_km_2lambda"], b["amp"])
for f in flip:
    print(f["z_wt_m"], "m:", f["dcc_pct"], "flip@", f["sign_flip_period_s"])
