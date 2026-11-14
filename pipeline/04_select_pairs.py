"""Station-pair selection for the St. Helens flank phase test.
Input : stations_msh.csv from 01_station_inventory.py
Output: pairs_msh.csv with, per band, whether the pair is usable.
Rules (docs/02 sec. 3): distance >= 2 wavelengths; distance <= max_km per band
(attenuation, Q ~30-100); both stations outside the crater exclusion radius;
both stations in the chosen flank sector (azimuth from summit); >= min_years
overlapping continuous record. Single-station (cross-component) entries are
always included for 2-8 Hz, where near-receiver coda dominates.
"""
import itertools
import numpy as np, pandas as pd
from obspy.geodetics import gps2dist_azimuth

SUMMIT = (46.200, -122.187)
CRATER_EXCL_KM = 3.0
SECTOR = (135, 315)            # S + W flanks (deg clockwise from N); north = debris avalanche
MIN_YEARS = 3
BANDS = {  # band: (wavelength_km, max_km)  from forward/band_design.json
    "0.5-1Hz": (3.16, 20), "1-2Hz": (1.30, 10), "2-4Hz": (0.55, 5), "4-8Hz": (0.23, 2.5)}

st = (pd.read_csv("stations_msh.csv")
        .groupby(["net", "sta"]).agg(lat=("lat", "first"), lon=("lon", "first"),
                                     start=("start", "min"), end=("end", "max")).reset_index())
d_az = [gps2dist_azimuth(*SUMMIT, r.lat, r.lon) for r in st.itertuples()]
st["r_km"] = [d[0] / 1e3 for d in d_az]; st["az"] = [d[1] for d in d_az]
keep = st[(st.r_km > CRATER_EXCL_KM) & st.az.between(*SECTOR)]
rows = []
for (_, a), (_, b) in itertools.combinations_with_replacement(keep.iterrows(), 2):
    ov = min(a.end, b.end) - max(a.start, b.start)
    if ov < MIN_YEARS:
        continue
    dist = 0.0 if a.sta == b.sta else gps2dist_azimuth(a.lat, a.lon, b.lat, b.lon)[0] / 1e3
    row = dict(sta1=f"{a.net}.{a.sta}", sta2=f"{b.net}.{b.sta}", dist_km=round(dist, 2),
               overlap_yr=round(ov, 1))
    for band, (lam, mx) in BANDS.items():
        if dist == 0:
            row[band] = band in ("2-4Hz", "4-8Hz") or band == "1-2Hz"   # self/cross-component
        else:
            row[band] = (dist >= 2 * lam) and (dist <= mx)
    rows.append(row)
out = pd.DataFrame(rows)
out.to_csv("pairs_msh.csv", index=False)
print(f"{len(keep)} flank stations, {len(out)} pairs/self-pairs;",
      {b: int(out[b].sum()) for b in BANDS})
