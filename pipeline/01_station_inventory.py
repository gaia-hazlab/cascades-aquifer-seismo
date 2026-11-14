"""Seismic station inventory per target: who recorded what, when.
Output: stations_<target>.csv  +  coverage_summary.csv
Answers: (i) years of continuous data available for dv/v,
         (ii) inter-station distances -> usable periods (>= ~1.5-3 wavelengths).
Run where FDSN is reachable (EarthScope for UW/CC/PB/etc., NCEDC for NC/BK).
"""
import itertools, sys
import numpy as np, pandas as pd
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.geodetics import gps2dist_azimuth
from targets import TARGETS

CHANNELS = "HH?,BH?,EH?,HN?,DP?,GP?"   # broadband, short-period, strong-motion, nodes/DAS-ish
CLIENTS = {"EARTHSCOPE": None, "NCEDC": None}

def query(t):
    rows = []
    for name in CLIENTS:
        try:
            c = CLIENTS[name] or Client(name)
            CLIENTS[name] = c
            inv = c.get_stations(latitude=t["lat"], longitude=t["lon"], maxradius=t["r"],
                                 channel=CHANNELS, level="channel")
        except Exception as e:
            print(f"  {name}: {e.__class__.__name__}", file=sys.stderr); continue
        for net in inv:
            for sta in net:
                for ch in sta:
                    rows.append(dict(dc=name, net=net.code, sta=sta.code, loc=ch.location_code,
                                     cha=ch.code, lat=sta.latitude, lon=sta.longitude,
                                     elev=sta.elevation, sr=ch.sample_rate,
                                     start=ch.start_date.year + ch.start_date.julday / 365,
                                     end=(ch.end_date or UTCDateTime()).year +
                                         (ch.end_date or UTCDateTime()).julday / 365))
    return pd.DataFrame(rows).drop_duplicates(["net", "sta", "loc", "cha", "start"])

def summarise(df):
    st = df.groupby(["net", "sta"]).agg(lat=("lat", "first"), lon=("lon", "first"),
                                        start=("start", "min"), end=("end", "max"),
                                        three_comp=("cha", lambda c: c.str[:2].value_counts().max() >= 3))
    st["years"] = st.end - st.start
    d = [gps2dist_azimuth(a.lat, a.lon, b.lat, b.lon)[0] / 1e3
         for (_, a), (_, b) in itertools.combinations(st.iterrows(), 2)]
    return st, np.array(d)

if __name__ == "__main__":
    summ = []
    for key, t in TARGETS.items():
        print(key)
        df = query(t)
        if df.empty:
            continue
        df.to_csv(f"stations_{key}.csv", index=False)
        st, d = summarise(df)
        long_ = st[st.years >= 5]
        summ.append(dict(target=key, n_sta=len(st), n_3c=int(st.three_comp.sum()),
                         n_ge5yr=len(long_), n_ge10yr=int((st.years >= 10).sum()),
                         median_pair_km=np.median(d) if len(d) else np.nan,
                         min_pair_km=d.min() if len(d) else np.nan,
                         # far-field rule of thumb: dist >= 2 wavelengths, c~2 km/s
                         max_period_s_median_pair=np.median(d) / (2 * 2.0) if len(d) else np.nan))
    pd.DataFrame(summ).to_csv("coverage_summary.csv", index=False)
    print(pd.DataFrame(summ).to_string())
