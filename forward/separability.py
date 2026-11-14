"""
How long must a dv/v record be to separate a groundwater-head term from
snow load and temperature, given red (AR1) noise?

Synthetic daily dv/v (fraction):
    dvv(t) = a_h * h(t) + a_s * SWE(t) + a_T * T_lag(t) + trend + noise
  h(t)   : head anomaly; seasonal sinusoid lagging snowmelt + decadal
           random-walk component (Cascade-crest wells swing several m on
           decadal cycles; Gannett & Lite 2013)
  SWE(t) : snowpack, peaks ~1 Apr, zero Jul-Oct
  T_lag  : air temperature diffused into the shallow subsurface (~30 d lag)
Regression: ordinary least squares on [h, SWE, T_lag, 1, t] with HAC
(Newey-West) standard errors. Report recovered a_h +/- 1 sigma vs record length.

Coefficients are set from the forward model (forward_results.json) for a
chosen beta0; defaults correspond to the Santiam-crest case, beta0 = 3e-7/Pa,
T ~ 0.7 s (head: -0.10 %/m, snow: +0.15 %/m SWE). Change them to test others.
"""
import numpy as np

rng = np.random.default_rng(42)


def forcing(n_years, h_season=2.0, h_decadal_std=3.0, swe_peak=1.0):
    t = np.arange(365 * n_years)
    doy = t % 365
    # snowpack: grows Nov->Apr 1, melts by early July
    swe = np.where((doy > 305) | (doy < 91),
                   swe_peak * (((doy - 305) % 365) / 151.0), 0.0)
    melt = (doy >= 91) & (doy < 182)
    swe[melt] = swe_peak * (1 - (doy[melt] - 91) / 91.0)
    swe *= 1 + 0.3 * rng.standard_normal(n_years).repeat(365)  # wet/dry years
    # head: seasonal peak ~ mid-July (lag after melt) + decadal drift
    seas = h_season * np.cos(2 * np.pi * (doy - 196) / 365)
    dec = np.cumsum(rng.standard_normal(n_years)) * h_decadal_std / np.sqrt(3)
    dec = np.interp(t, np.arange(n_years) * 365 + 182, dec)
    h = seas + dec
    # temperature: annual cycle, peak late Jul, diffused with ~30 d lag
    T = 10 * np.cos(2 * np.pi * (doy - 205 - 30) / 365)
    return t, h, swe, T


def ar1(n, sigma, phi=0.9):
    e = np.zeros(n)
    w = rng.standard_normal(n) * sigma * np.sqrt(1 - phi ** 2)
    for i in range(1, n):
        e[i] = phi * e[i - 1] + w[i]
    return e


def newey_west(X, resid, L=60):
    n = len(resid)
    XtXi = np.linalg.inv(X.T @ X)
    S = (X * resid[:, None]).T @ (X * resid[:, None])
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        G = (X[l:] * resid[l:, None]).T @ (X[:-l] * resid[:-l, None])
        S += w * (G + G.T)
    return np.sqrt(np.diag(XtXi @ S @ XtXi))


def trial(n_years, a_h=-1.0e-3, a_s=1.5e-3, a_T=2e-5, sigma=2e-4):
    t, h, swe, T = forcing(n_years)
    y = a_h * h + a_s * swe + a_T * T + 1e-6 * t / 365 + ar1(len(t), sigma)
    X = np.column_stack([h, swe, T, np.ones_like(t), t / 365.0])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    se = newey_west(X, y - X @ coef)
    return coef[0], se[0], np.corrcoef(h, swe)[0, 1]


if __name__ == "__main__":
    print("years | a_h true -1.00e-3 /m | recovered (median of 50) | 1σ | detect (|a|>3σ) | corr(h,SWE)")
    for ny in [1, 2, 3, 5, 10, 20]:
        rs = [trial(ny) for _ in range(50)]
        a = np.median([r[0] for r in rs]); s = np.median([r[1] for r in rs])
        det = np.mean([abs(r[0]) > 3 * r[1] for r in rs])
        c = np.median([r[2] for r in rs])
        print(f"{ny:5d} | {a: .2e} | ±{s:.1e} | {det:4.0%} | {c:+.2f}")
    print("\nSame, weak case (beta0=3e-8: a_h=-1e-4/m, a_s=+1.5e-4/m):")
    for ny in [2, 5, 10, 20]:
        rs = [trial(ny, a_h=-1e-4, a_s=1.5e-4) for _ in range(50)]
        det = np.mean([abs(r[0]) > 3 * r[1] for r in rs])
        print(f"{ny:5d} yr: detection rate {det:4.0%}, median 1σ ±{np.median([r[1] for r in rs]):.1e}")
