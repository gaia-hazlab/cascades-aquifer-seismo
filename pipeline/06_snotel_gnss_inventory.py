"""SNOTEL and GNSS station inventory per target box.
Output: snotel_sites_<target>.csv (NRCS AWDB REST station list, network SNTL)
        gnss_sites_<target>.csv   (Nevada Geodetic Laboratory DataHoldings.txt:
                                   sta, lat, lon, height_m, first, last solution date)
        obs_inventory_summary.csv (counts per target)
GNSS dates are first/last daily solution, not completeness.
"""
import pandas as pd, requests
from targets import TARGETS, bbox

AWDB = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"
NGL = "https://geodesy.unr.edu/NGLStationPages/DataHoldings.txt"
STATES = {"msh": "WA", "adams": "WA", "indian_heaven": "WA", "santiam_pass": "OR",
          "three_sisters": "OR", "shasta": "CA", "medicine_lake": "CA", "lassen": "CA"}

def inbox(df, t, lat="lat", lon="lon"):
    b = bbox(t)
    return df[df[lon].between(b[0], b[2]) & df[lat].between(b[1], b[3])]

if __name__ == "__main__":
    sn = {s: pd.DataFrame(requests.get(AWDB, params=dict(stationTriplets=f"*:{s}:SNTL"),
                                       timeout=120).json()) for s in set(STATES.values())}
    rows = [l.split()[:10] for l in requests.get(NGL, timeout=120).text.splitlines()[1:]
            if len(l.split()) >= 10]
    g = pd.DataFrame(rows).iloc[:, [0, 1, 2, 3, 7, 8]]
    g.columns = ["sta", "lat", "lon", "height_m", "first", "last"]
    g[["lat", "lon", "height_m"]] = g[["lat", "lon", "height_m"]].astype(float)
    g["lon"] = g.lon.where(g.lon <= 180, g.lon - 360)
    summ = []
    for key, t in TARGETS.items():
        s = inbox(sn[STATES[key]], t, "latitude", "longitude")[
            ["stationTriplet", "name", "latitude", "longitude", "elevation", "beginDate", "endDate"]]
        x = inbox(g, t)
        s.to_csv(f"snotel_sites_{key}.csv", index=False)
        x.to_csv(f"gnss_sites_{key}.csv", index=False)
        yrs = (pd.to_datetime(x["last"]) - pd.to_datetime(x["first"])).dt.days / 365.25
        summ.append(dict(target=key, n_snotel=len(s), n_gnss=len(x),
                         n_gnss_ge10yr=int((yrs >= 10).sum()),
                         n_gnss_active_2026=int((x["last"] >= "2026-01-01").sum())))
    pd.DataFrame(summ).to_csv("obs_inventory_summary.csv", index=False)
    print(pd.DataFrame(summ).to_string(index=False))
