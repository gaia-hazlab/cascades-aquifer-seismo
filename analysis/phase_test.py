"""
Falsification test for an aquifer contribution to dv/v.

Hypothesis H1 (aquifer):   dv/v(t) = a*SWE(t) + b*H_tau(t) + c*T_lag(t) + trend + e,  b < 0
  H_tau = melt+rain input convolved with exp(-t/tau)/tau  (lumped head response;
          tau relates to hydraulic diffusivity D ~ L^2 / tau for flow-path scale L)
Null H0 (no aquifer term): same without H_tau.

Outputs per band: best tau, b (+/- block-bootstrap CI over water years), delta-AIC(H0 - H1),
and a verdict:
  SUPPORTS  : b < 0 with 95 % CI excluding 0, dAIC > 10, tau within [tau_lo, tau_hi]
  AMBIGUOUS : b < 0 but CI touches 0 or dAIC in (2, 10]
  FAILS     : b >= 0, or dAIC <= 2
Default plausible tau range 20-200 days (MODFLOW hillslope: head peaks ~12 weeks after
melt onset). Inputs are plain CSVs so this runs on anyone's dv/v product:
  dvv.csv   : date, band, dvv  (fraction or %, set --percent), [err]
  forcing.csv: date, swe_m, precip_m, [tair_c]   (e.g. from pipeline/03_snotel.py)
Run:  python phase_test.py --dvv dvv.csv --forcing forcing.csv
      python phase_test.py --selftest
"""
import argparse, json
import numpy as np
import pandas as pd

TAUS = np.array([5, 10, 20, 30, 45, 60, 90, 120, 150, 200, 300])


def recharge_input(f):
    """Liquid water input: snowmelt (-dSWE when positive) + rain falling on no snow."""
    dswe = f["swe_m"].diff().fillna(0)
    melt = (-dswe).clip(lower=0)
    rain = f["precip_m"].where(f["swe_m"] <= 0.01, 0.0) if "precip_m" in f else 0.0
    return (melt + rain).values


def conv_exp(x, tau):
    k = np.exp(-np.arange(int(6 * tau)) / tau); k /= k.sum()
    return np.convolve(x, k)[: len(x)]


def design(f, tau=None, lag_T=30):
    t = (f.index - f.index[0]).days.values / 365.25
    cols = [f["swe_m"].values]
    if "tair_c" in f:
        cols.append(f["tair_c"].rolling(lag_T, min_periods=1).mean().values)
    if tau is not None:
        h = conv_exp(recharge_input(f), tau); cols.append(h - h.mean())
    cols += [np.ones_like(t), t]
    return np.column_stack(cols)


def fit(y, X, n_eff=None):
    """OLS. AIC uses an effective sample size: daily dv/v residuals are strongly
    autocorrelated, and AIC with raw n inflates dAIC (false 'aquifer' detections)."""
    ok = np.isfinite(y)
    beta, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None)
    r = y[ok] - X[ok] @ beta
    n = n_eff if n_eff is not None else ok.sum()
    aic = n * np.log(np.mean(r ** 2)) + 2 * X.shape[1]
    return beta, aic, r


def effective_n(r):
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    rho = min(max(rho, 0.0), 0.999)
    return len(r) * (1 - rho) / (1 + rho)


def test_band(y, f, n_boot=300, rng=np.random.default_rng(0), tau_lo=20, tau_hi=200):
    i_h = 2 if "tair_c" in f else 1
    _, _, r0 = fit(y, design(f))
    neff = effective_n(r0)                       # from the null-model residuals
    _, aic0, _ = fit(y, design(f), neff)
    fits = [(tau, *fit(y, design(f, tau), neff)[:2]) for tau in TAUS]
    tau, beta, aic1 = min(fits, key=lambda z: z[2])
    b = beta[i_h]
    # block bootstrap over water years (keeps seasonal autocorrelation)
    wy = (f.index + pd.offsets.DateOffset(months=3)).year.values
    years = np.unique(wy); bs = []
    for _ in range(n_boot):
        pick = rng.choice(years, len(years))
        idx = np.concatenate([np.where(wy == yy)[0] for yy in pick])
        bb, _, _ = fit(y[idx], design(f, tau)[idx]); bs.append(bb[i_h])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    daic = aic0 - aic1
    if b < 0 and hi < 0 and daic > 10 and tau_lo <= tau <= tau_hi:
        verdict = "SUPPORTS"
    elif b < 0 and daic > 2:
        verdict = "AMBIGUOUS"
    else:
        verdict = "FAILS"
    return dict(tau_days=int(tau), b=float(b), b_ci95=[float(lo), float(hi)],
                dAIC=float(daic), n_eff=float(neff), n_years=int(len(years)), verdict=verdict)


def selftest():
    """Synthetic: 6 water years, snow loading +, head response - with tau=60 d, AR(1) noise."""
    rng = np.random.default_rng(1)
    d = pd.date_range("2016-10-01", "2022-09-30", freq="D")
    doy = d.dayofyear.values
    peak = 1.0 + 0.3 * rng.standard_normal(len(np.unique(d.year)))
    yr_peak = dict(zip(np.unique(d.year), peak))
    swe = np.array([yr_peak[yy] * (max(0, 1 - abs(((dd - 91) % 365) - 0) / 150) if (dd < 91 or dd > 305)
                    else max(0, 1 - (dd - 91) / 90)) for yy, dd in zip(d.year, doy)])
    swe = np.clip(swe, 0, None)
    f = pd.DataFrame(dict(swe_m=swe, precip_m=0.004 * (rng.random(len(d)) < 0.3)), index=d)
    h = conv_exp(recharge_input(f), 60); h -= h.mean()
    e = np.zeros(len(d)); w = rng.standard_normal(len(d)) * 2e-5
    for i in range(1, len(d)):
        e[i] = 0.95 * e[i - 1] + w[i]
    res = {}
    for name, b_true in [("aquifer_present", -0.08), ("snow_only", 0.0)]:
        y = 1.2e-4 * swe + b_true * h + e
        res[name] = test_band(y, f)
    print(json.dumps(res, indent=1))
    assert res["aquifer_present"]["verdict"] == "SUPPORTS", res
    assert res["snow_only"]["verdict"] == "FAILS", res
    print("selftest passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dvv"); ap.add_argument("--forcing")
    ap.add_argument("--percent", action="store_true", help="dv/v given in %")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="phase_test_results.json")
    a = ap.parse_args()
    if a.selftest:
        selftest(); raise SystemExit
    dv = pd.read_csv(a.dvv, parse_dates=["date"])
    fo = pd.read_csv(a.forcing, parse_dates=["date"]).set_index("date").asfreq("D").interpolate(limit=5)
    out = {}
    for band, g in dv.groupby("band"):
        y = g.set_index("date")["dvv"].asfreq("D").reindex(fo.index)
        y = (y / 100 if a.percent else y).values
        out[band] = test_band(y, fo)
        print(band, out[band])
    json.dump(out, open(a.out, "w"), indent=1)
