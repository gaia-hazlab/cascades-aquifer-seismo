"""
Synthetic feasibility test: can ambient-noise dv/v (and static Rayleigh
tomography) see groundwater in Cascade fractured-lava aquifers?

Physics (1-D, laterally uniform, fundamental-mode Rayleigh):
  (1) Pore-pressure (effective-stress) effect below the water table:
        dlnVs(z) = -beta(z) * rho_w g dh,  beta(z) = beta0 * exp(-sigma_eff(z)/sigma_c)
      (crack-closure stress sensitivity; Shapiro 2003-style piezosensitivity)
  (2) Saturation of fractures in the band swept by the water table:
        Gassmann-like: Vs drops by density only, Vp rises (compliant cracks).
  (3) Snow load (areal, wide relative to depth): uniform vertical stress
        increase d_sigma = rho_w g SWE, partially undrained (Skempton B):
        dlnVs(z) = +beta(z) * (1-B) * d_sigma
Observable: dc/c(T) computed by direct forward modelling (disba) of base vs
perturbed model, cross-checked against linearised Vs/Vp kernels.

All numbers are PRIORS, not measurements. beta0 and sigma_c are the least
constrained parameters; results are reported as a function of beta0.
"""
import json
import numpy as np
from disba import PhaseDispersion, PhaseSensitivity, Ellipticity

RHO_W, G = 1000.0, 9.81                       # kg/m3, m/s2
PERIODS = np.array([0.25, 0.35, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0])  # s

# ---------------- base model: young High Cascades lavas ----------------
# (depth_top_km, Vp, Vs, rho) -- generic prior; replace with iMUSH /
# Wang et al. 2017 / local 1-D model per site.
COARSE = [
    (0.00, 2.6, 1.40, 2.10),   # rubbly / fractured flow tops, scoria
    (0.20, 3.8, 2.10, 2.35),   # stacked fractured basaltic-andesite flows
    (1.00, 4.8, 2.75, 2.55),
    (2.00, 5.6, 3.20, 2.65),
    (4.00, 6.0, 3.45, 2.70),
    (8.00, 6.3, 3.65, 2.75),   # half-space
]
DZ = 0.02   # km, fine layering to 3 km


def build_model():
    tops = [c[0] for c in COARSE]
    z = np.arange(0, 3.0, DZ)
    rows = []
    for zt in z:
        i = np.searchsorted(tops, zt, side="right") - 1
        rows.append([DZ, *COARSE[i][1:]])
    for c, nxt in zip(COARSE[3:], COARSE[4:] + [None]):
        if c[0] < 3.0:
            continue
    rows.append([1.0, *COARSE[3][1:]])   # 3-4 km
    rows.append([4.0, *COARSE[4][1:]])   # 4-8 km
    rows.append([10.0, *COARSE[5][1:]])  # half-space
    m = np.array(rows)                   # thickness, vp, vs, rho
    zmid = np.cumsum(m[:, 0]) - m[:, 0] / 2
    return m, zmid


def phase_c(m):
    pd = PhaseDispersion(*m.T, dc=0.0001)
    return pd(PERIODS, mode=0, wave="rayleigh").velocity


def sigma_eff_MPa(m, zmid, z_wt_km):
    """Vertical effective stress (MPa) at layer midpoints."""
    rho = m[:, 3] * 1000
    sv = np.cumsum(rho * G * m[:, 0] * 1000) - rho * G * m[:, 0] * 500
    pp = np.where(zmid > z_wt_km, RHO_W * G * (zmid - z_wt_km) * 1000, 0.0)
    return (sv - pp) / 1e6


def beta_profile(m, zmid, z_wt, beta0, sigma_c):
    return beta0 * np.exp(-sigma_eff_MPa(m, zmid, z_wt) / sigma_c)  # 1/Pa


def perturb(m, zmid, *, z_wt, dh=0.0, swe=0.0, beta0=1e-7, sigma_c=10.0,
            phi=0.05, B=0.5, sat_vp_gain=0.15):
    """Return perturbed model. dh>0 = water table rises by dh (m)."""
    p = m.copy()
    beta = beta_profile(m, zmid, z_wt, beta0, sigma_c)
    dlnvs = np.zeros(len(m))
    dlnvp = np.zeros(len(m))
    # (1) pore pressure below the (new) water table
    below = zmid > (z_wt - dh / 1000)
    dlnvs[below] += -beta[below] * RHO_W * G * dh
    dlnvp[below] += -beta[below] * RHO_W * G * dh
    # (2) saturation of band swept by the rising water table
    drho_l = np.zeros(len(m))
    if dh > 0:
        top = np.cumsum(m[:, 0]) - m[:, 0]
        bot = np.cumsum(m[:, 0])
        lo, hi = z_wt - dh / 1000, z_wt            # swept band (km)
        frac = np.clip((np.minimum(bot, hi) - np.maximum(top, lo)) / m[:, 0], 0, 1)
        drho_l = frac * phi * RHO_W / (m[:, 3] * 1000)
        dlnvs += -0.5 * drho_l
        dlnvp += frac * sat_vp_gain - 0.5 * drho_l
    # (3) snow load
    if swe:
        dlnvs += beta * (1 - B) * RHO_W * G * swe
        dlnvp += beta * (1 - B) * RHO_W * G * swe
    p[:, 1] *= 1 + dlnvp
    p[:, 2] *= 1 + dlnvs
    p[:, 3] *= 1 + drho_l
    return p


def dcc(m, p, c0):
    return (phase_c(p) - c0) / c0


def kernels(m):
    """Linearised dlnc/dlnV per layer (for cross-check + depth plot)."""
    ps = PhaseSensitivity(*m.T)
    out = {}
    for T in [0.35, 1.0, 3.0]:
        kvs = ps(T, mode=0, wave="rayleigh", parameter="velocity_s")
        kvp = ps(T, mode=0, wave="rayleigh", parameter="velocity_p")
        c = kvs.velocity
        out[T] = (kvs.kernel * m[:, 2] / c, kvp.kernel * m[:, 1] / c)
    return out


SITES = {
    # z_wt: water-table depth (km); seasonal/decadal dh (m); peak SWE (m)
    # Priors from: Gannett & Lite 2013 (Cascade-margin wells: >6 m decadal),
    # Karlstrom et al. 2025 (deep vertical flow at crest -> deep WT),
    # Makus et al. 2024 (seasonal GW-driven dv/v at MSH).
    "Santiam_crest_OR": dict(z_wt=0.20, dh_season=2.0, dh_decade=8.0, swe=1.0),
    "MSH_flank_WA":     dict(z_wt=0.03, dh_season=3.0, dh_decade=4.0, swe=1.0),
    "Shasta_MLV_CA":    dict(z_wt=0.25, dh_season=1.0, dh_decade=6.0, swe=0.6),
}
BETAS = [3e-9, 3e-8, 3e-7]   # 1/Pa at zero effective stress
NOISE = 2e-4                 # 0.02 % : optimistic multi-pair, 10-day stack


def main():
    m, zmid = build_model()
    c0 = phase_c(m)
    res = {"periods_s": PERIODS.tolist(), "c0_kms": c0.round(4).tolist(),
           "noise_dvv": NOISE, "sites": {}}

    # finite-difference sanity: tiny uniform Vs perturbation in top 0.5 km
    t = m.copy(); t[zmid < 0.5, 2] *= 1 + 1e-3
    fd = dcc(m, t, c0)
    K = kernels(m)
    lin = {T: float(np.sum(K[T][0][zmid < 0.5]) * 1e-3) for T in K}
    res["check_fd_vs_linear"] = {"fd": dict(zip(PERIODS.tolist(), fd.round(7).tolist())),
                                 "linear": lin}

    for site, s in SITES.items():
        r = {}
        for b in BETAS:
            seas = dcc(m, perturb(m, zmid, z_wt=s["z_wt"], dh=s["dh_season"], beta0=b), c0)
            deca = dcc(m, perturb(m, zmid, z_wt=s["z_wt"], dh=s["dh_decade"], beta0=b), c0)
            snow = dcc(m, perturb(m, zmid, z_wt=s["z_wt"], swe=s["swe"], beta0=b), c0)
            sat_only = dcc(m, perturb(m, zmid, z_wt=s["z_wt"], dh=s["dh_season"],
                                      beta0=0.0), c0)
            r[f"beta0={b:.0e}"] = {
                "seasonal_head_%": (100 * seas).round(4).tolist(),
                "decadal_head_%": (100 * deca).round(4).tolist(),
                "snow_load_%": (100 * snow).round(4).tolist(),
                "saturation_only_%": (100 * sat_only).round(5).tolist(),
            }
        res["sites"][site] = {"priors": s, "dc/c": r}

    # ---- static tomography question: dry vs saturated fractured column ----
    # saturating 0.2-1.0 km: Vp +15 %, Vs -1 % (density only), rho +2 %
    sat = m.copy()
    zone = (zmid > 0.2) & (zmid < 1.0)
    sat[zone, 1] *= 1.15; sat[zone, 2] *= 0.99; sat[zone, 3] *= 1.02
    res["static_saturated_vs_dry_%"] = (100 * dcc(m, sat, c0)).round(3).tolist()
    try:
        e0 = Ellipticity(*m.T)(PERIODS, mode=0).ellipticity
        e1 = Ellipticity(*sat.T)(PERIODS, mode=0).ellipticity
        res["static_HV_ellipticity_change_%"] = (100 * (e1 - e0) / e0).round(2).tolist()
    except Exception as exc:   # ellipticity can fail at short periods
        res["static_HV_ellipticity_change_%"] = f"failed: {exc}"

    # kernel depth of max sensitivity (for geometry discussion)
    res["kernel_peak_depth_km"] = {str(T): float(zmid[np.argmax(np.abs(K[T][0]) / m[:, 0])])
                                   for T in K}
    res["kernel_vp_fraction"] = {str(T): float(np.sum(np.abs(K[T][1])) /
                                 (np.sum(np.abs(K[T][0])) + np.sum(np.abs(K[T][1]))))
                                 for T in K}
    json.dump(res, open("forward_results.json", "w"), indent=1)

    # ---------- figure ----------
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    for T, (kvs, kvp) in K.items():
        ax[0].plot(kvs / m[:, 0], zmid, label=f"Vs, T={T}s")
        ax[0].plot(kvp / m[:, 0], zmid, "--", label=f"Vp, T={T}s")
    ax[0].set_ylim(4, 0); ax[0].set_xlabel("dlnc/dlnV per km"); ax[0].set_ylabel("depth (km)")
    ax[0].axhspan(0.2, 1.0, color="tab:blue", alpha=0.08, label="target aquifer")
    ax[0].legend(fontsize=7); ax[0].set_title("Rayleigh phase-velocity kernels")
    for site, col in zip(SITES, ["tab:blue", "tab:green", "tab:purple"]):
        for key, ls in [("seasonal_head_%", "-o"), ("decadal_head_%", "--s"), ("snow_load_%", ":^")]:
            y = [max(np.abs(res["sites"][site]["dc/c"][f"beta0={b:.0e}"][key])) for b in BETAS]
            ax[1].loglog(BETAS, y, ls, color=col, ms=4,
                         label=f"{site} {key.split('_')[0]}")
    ax[1].axhline(300 * NOISE, color="k", lw=1, label="3σ (0.06 %)")
    ax[1].set_xlabel("beta0, stress sensitivity at zero eff. stress (1/Pa)")
    ax[1].set_ylabel("max |dc/c| over 0.25-5 s (%)")
    ax[1].set_title("Detectability vs stress sensitivity"); ax[1].legend(fontsize=6)
    fig.tight_layout(); fig.savefig("forward_feasibility.png", dpi=150)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
