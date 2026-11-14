"""Minimal, dependency-light stretching dv/v (Sens-Schoenfelder & Wegler 2006
convention: a homogeneous velocity increase dv/v = eps compresses the coda,
cur(t) = ref(t*(1+eps))). For quick checks on correlation stacks; use SeisMIC
(pip install seismic) or NoisePy for production: they handle preprocessing,
station changes, spatial inversion (SeisMIC) and QC.
"""
import numpy as np

def stretch(ref, cur, t, tmin, tmax, eps_max=0.01, n=401, both_lags=True):
    """Return (dv/v, CC, error). t symmetric lag axis (s)."""
    eps = np.linspace(-eps_max, eps_max, n)
    win = (np.abs(t) >= tmin) & (np.abs(t) <= tmax) if both_lags else (t >= tmin) & (t <= tmax)
    c = cur[win]; c = (c - c.mean()) / (np.linalg.norm(c - c.mean()) + 1e-30)
    cc = np.empty(n)
    for i, e in enumerate(eps):
        r = np.interp(t[win] * (1 + e), t, ref)
        r = (r - r.mean()) / (np.linalg.norm(r - r.mean()) + 1e-30)
        cc[i] = r @ c
    k = int(np.argmax(cc))
    if 0 < k < n - 1:                      # parabolic refinement
        y0, y1, y2 = cc[k - 1:k + 2]
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
        e_best = eps[k] + d * (eps[1] - eps[0])
    else:
        e_best = eps[k]
    # Weaver et al. (2011): rms = sqrt(1-X^2)/(2X) * sqrt(6 sqrt(pi/2) Tb / (wc^2 (t2^3 - t1^3)))
    fc, bw = _freq_stats(ref, t)
    X = min(max(cc[k], 1e-6), 1 - 1e-12)
    err = np.sqrt(1 - X ** 2) / (2 * X) * np.sqrt(
        6 * np.sqrt(np.pi / 2) * (1 / bw) / ((2 * np.pi * fc) ** 2 * (tmax ** 3 - tmin ** 3)))
    return e_best, cc[k], err

def _freq_stats(x, t):
    f = np.fft.rfftfreq(len(x), t[1] - t[0]); P = np.abs(np.fft.rfft(x)) ** 2
    fc = (f * P).sum() / P.sum()
    return float(fc), float(np.sqrt(((f - fc) ** 2 * P).sum() / P.sum()))

def _synthetic_coda(t, f0=1.0, tau=20.0, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(len(t))
    F = np.fft.rfft(x); f = np.fft.rfftfreq(len(t), t[1] - t[0])
    F *= np.exp(-((f - f0) / (0.5 * f0)) ** 2)
    x = np.fft.irfft(F, len(t)); x = 0.5 * (x + x[::-1])
    return x * np.exp(-np.abs(t) / tau)

if __name__ == "__main__":
    dt = 0.05; t = np.arange(-60, 60 + dt, dt)
    ref = _synthetic_coda(t)
    rng = np.random.default_rng(1)
    print("true dv/v | est dv/v | CC | 1-sigma (Weaver) | noise")
    for true in [-5e-3, -1e-3, 2e-4, 1e-3]:
        for snr_noise in [0.0, 0.2]:
            cur = np.interp(t * (1 + true), t, ref)          # velocity change -> stretch
            cur = cur + snr_noise * ref.std() * rng.standard_normal(len(t))
            e, c, s = stretch(ref, cur, t, 5, 40, eps_max=0.01, n=801)
            print(f"{true: .1e} | {e: .2e} | {c:.3f} | {s:.1e} | {snr_noise}")
            assert abs(e - true) < max(3 * s, 5e-5), "stretching test failed"
    print("all synthetic stretching tests passed")
