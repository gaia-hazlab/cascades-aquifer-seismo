"""Hydrologic inventory per target via the USGS Water Data OGC API
(dataretrieval >= 1.4, module `waterdata`). Pulls:
  wells (GW), springs (SP), streams (ST) inside each target bbox;
  daily discharge (00060) for streams/springs;
  groundwater-level field measurements (72019, depth below land surface).
Output: hydro_sites_<target>.csv, discharge_<target>.parquet, gwlevels_<target>.parquet,
        hydro_summary.csv  (record length, n obs, seasonal amplitude).
State databases (OWRD well logs, WA Ecology well reports, CA DWR) are NOT
covered here -- see README section 4.
"""
import sys
import pandas as pd
from dataretrieval import waterdata as wd
from dataretrieval import ngwmn   # WA Ecology (WAECY) and other state wells
from targets import TARGETS, bbox

def get(fn, **kw):
    try:
        df, _ = fn(**kw); return df
    except Exception as e:
        print(f"  {fn.__name__}: {e.__class__.__name__}: {e}", file=sys.stderr)
        return pd.DataFrame()

def seasonal_amp(s):
    """Median annual (max-min) of a daily or sparse series."""
    s = s.dropna()
    if s.empty: return float("nan")
    g = s.groupby(s.index.year)
    r = (g.max() - g.min())[g.count() >= 4]
    return float(r.median()) if len(r) else float("nan")

if __name__ == "__main__":
    out = []
    for key, t in TARGETS.items():
        print(key)
        sites = get(wd.get_monitoring_locations, bbox=bbox(t),
                    site_type_code=["GW", "SP", "ST"], skip_geometry=True)
        if sites.empty: continue
        sites.to_csv(f"hydro_sites_{key}.csv", index=False)
        ids = sites["id"].tolist() if "id" in sites else sites["monitoring_location_id"].tolist()
        q = get(wd.get_daily, monitoring_location_id=ids, parameter_code="00060",
                statistic_id="00003", skip_geometry=True)
        gw = get(wd.get_field_measurements, monitoring_location_id=ids,
                 parameter_code="72019", skip_geometry=True)
        for name, df in [("discharge", q), ("gwlevels", gw)]:
            if df.empty: continue
            df["time"] = pd.to_datetime(df["time"]); df.to_parquet(f"{name}_{key}.parquet")
            for sid, g in df.groupby("monitoring_location_id"):
                s = g.set_index("time")["value"].astype(float).sort_index()
                out.append(dict(target=key, kind=name, site=sid, n=len(s),
                                first=s.index.min().date(), last=s.index.max().date(),
                                years=(s.index.max() - s.index.min()).days / 365.25,
                                seasonal_range=seasonal_amp(s),
                                cv=float(s.std() / s.mean()) if s.mean() else float("nan")))
        # NGWMN: state-agency wells (e.g. agency_code WAECY = WA Ecology) not in NWIS
        ng = get(ngwmn.get_sites, bbox=bbox(t), skip_geometry=True)
        if not ng.empty:
            ng.to_csv(f"ngwmn_sites_{key}.csv", index=False)
            idcol = "monitoring_location_id" if "monitoring_location_id" in ng else "id"
            wl = get(ngwmn.get_water_level, monitoring_location_id=ng[idcol].tolist())
            if not wl.empty:
                wl.to_parquet(f"ngwmn_wl_{key}.parquet")
                tcol = "sample_time" if "sample_time" in wl else "datetime"
                for sid, g in wl.groupby("monitoring_location_id"):
                    tt = pd.to_datetime(g[tcol])
                    out.append(dict(target=key, kind="ngwmn_wl", site=sid, n=len(g),
                                    first=tt.min().date(), last=tt.max().date(),
                                    years=(tt.max() - tt.min()).days / 365.25,
                                    seasonal_range=float("nan"), cv=float("nan")))
    pd.DataFrame(out).to_csv("hydro_summary.csv", index=False)
    print(pd.DataFrame(out).sort_values(["target", "kind", "years"], ascending=[True, True, False])
          .groupby(["target", "kind"]).head(5).to_string())
