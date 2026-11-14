"""
MODFLOW 6 (FloPy) 2-D hillslope cross-section of a young Cascade volcano flank.
Purpose: test whether the water-table depth and seasonal swing priors used in
the dv/v forward model are physically consistent, and produce head time series
that feed the dv/v observation operator (forward_dvv.perturb).

Domain : 8 km from drainage divide (x=0, 2000 m asl) to valley river (x=8 km,
         800 m asl); 1.5 km thick, layers follow topography.
K(z)   : Saar & Manga (2004), Oregon Cascades:
         k = 5e-13 exp(-z/250 m) m^2 (z <= 0.8 km); k = 1e-14 (z/1 km)^-3.2 below.
         K = k * rho g / mu (~1e7 k). Isotropic (high Kv per Karlstrom et al. 2025).
Storage: Ss = 5.5e-6 1/m (Saar & Manga 2003); Sy in {0.02, 0.05, 0.10}.
Recharge: mean 0.75 m/yr (Saar & Manga: 0.5-1 m/yr), 70 % as Apr-Jun snowmelt,
         30 % as Oct-Dec rain. Spin-up steady state + 6 periodic years.
BCs    : no-flow divide and base; drains on every top cell at land surface
         (springs / seepage faces, cap water table at surface); river = drain.
Run    : python hillslope_mf6.py   (needs `mf6` on PATH; flopy >= 3.8)
"""
import json, sys, pathlib
import numpy as np
import flopy

WS = pathlib.Path("mf6_ws"); WS.mkdir(exist_ok=True)
L, NCOL = 8000.0, 80
DX = L / NCOL
X = (np.arange(NCOL) + 0.5) * DX
TOP = 2000.0 - 1200.0 * (X / L) ** 0.8              # concave volcano flank
THK = np.geomspace(5, 150, 30); THK *= 1500 / THK.sum()
NLAY = len(THK)
BOT = TOP[None, :] - np.cumsum(THK)[:, None]
ZMID = (np.cumsum(THK) - THK / 2)[:, None] * np.ones((1, NCOL))   # depth below surface


def k_of_z(z):
    zk = z / 1000.0
    return np.where(zk <= 0.8, 5e-13 * np.exp(-z / 250.0), 1e-14 * np.maximum(zk, 0.8) ** -3.2)


KH = k_of_z(ZMID) * 1e7                              # m/s
KH_DAY = KH * 86400


def recharge_series(n_years, mean_m_yr=0.75):
    """Weekly recharge (m/d) for n_years: 70 % Apr-Jun, 30 % Oct-Dec."""
    weeks = np.arange(52 * n_years); woy = weeks % 52
    r = np.zeros(len(weeks))
    melt = (woy >= 13) & (woy < 26); rain = (woy >= 39) & (woy < 52)
    r[melt] = 0.7 * mean_m_yr / 13 / 7
    r[rain] = 0.3 * mean_m_yr / 13 / 7
    return r


def run(sy, n_years=6, name="hs"):
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(WS), exe_name="mf6")
    rch = recharge_series(n_years)
    pd = [(365.25 * 50, 50, 1.2)] + [(7.0, 1, 1.0)] * len(rch)
    flopy.mf6.ModflowTdis(sim, nper=len(pd), perioddata=pd, time_units="days")
    flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                         outer_maximum=2000, inner_maximum=500,
                         outer_dvclose=1e-3, inner_dvclose=1e-5,
                         under_relaxation="DBD", backtracking_number=20)
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name, newtonoptions="UNDER_RELAXATION",
                               save_flows=False)
    flopy.mf6.ModflowGwfdis(gwf, nlay=NLAY, nrow=1, ncol=NCOL, delr=DX, delc=1.0,
                            top=TOP, botm=BOT[:, None, :])
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=1, k=KH_DAY[:, None, :])
    sto = flopy.mf6.ModflowGwfsto(gwf, iconvert=1, ss=5.5e-6, sy=sy,
                                  transient={0: True})
    flopy.mf6.ModflowGwfic(gwf, strt=np.broadcast_to(TOP - 5.0, (NLAY, 1, NCOL)).copy())
    # drains: seepage at land surface everywhere in the top layer (springs/river)
    cond = KH_DAY[0] * DX
    drn = [[(0, 0, j), TOP[j], cond[j]] for j in range(NCOL)]
    flopy.mf6.ModflowGwfdrn(gwf, stress_period_data={0: drn})
    rspd = {0: [[(0, 0, j), rch.mean()] for j in range(NCOL)]}
    for i, r in enumerate(rch):
        rspd[i + 1] = [[(0, 0, j), r] for j in range(NCOL)]
    flopy.mf6.ModflowGwfrcha(gwf, recharge={k: v[0][1] for k, v in rspd.items()})
    flopy.mf6.ModflowGwfoc(gwf, head_filerecord=f"{name}.hds",
                           saverecord=[("HEAD", "ALL")])
    sim.write_simulation(silent=True)
    ok, buff = sim.run_simulation(silent=True)
    if not ok:
        print("\n".join(buff[-20:])); sys.exit(1)
    hds = gwf.output.head().get_alldata()            # (ntimes, nlay, 1, ncol)
    hds = np.where(hds > 1e20, np.nan, hds)
    hds = np.where(hds < -1e20, np.nan, hds)
    wt = np.nanmax(hds[:, :, 0, :], axis=1)          # water table = max head in column
    return wt, rch


if __name__ == "__main__":
    res = {}
    obs_x = [1000, 3000, 5000, 7000]
    jj = [int(x // DX) for x in obs_x]
    for sy in [0.02, 0.05, 0.10]:
        wt, rch = run(sy, name=f"hs_sy{int(sy*100):02d}")
        last = wt[-52:]                              # final periodic year
        r = {}
        for x, j in zip(obs_x, jj):
            depth = TOP[j] - np.minimum(last[:, j], TOP[j])   # head above land = discharge zone
            lag_w = int(np.argmax(last[:, j]) - 13)  # weeks after melt onset (week 13)
            r[f"x{x//1000}km"] = dict(discharge_zone=bool((last[:, j] >= TOP[j]).mean() > 0.5),
                                      mean_wt_depth_m=round(float(depth.mean()), 1),
                                      seasonal_range_m=round(float(np.ptp(last[:, j])), 2),
                                      peak_lag_weeks_after_melt_onset=lag_w)
        res[f"Sy={sy}"] = r
        np.save(WS / f"wt_sy{int(sy*100):02d}.npy", wt)
    json.dump(res, open("hillslope_results.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
