"""Waveform availability for the stations in pairs_msh.csv (HANDOFF task 3 follow-up).
Input : pairs_msh.csv
Output: availability_daily_msh.csv   (sta, cha, date, pct) daily percent availability
        availability_summary_msh.csv (per station: channels, first/last day, days with
                                      >= MIN_PCT % data, fraction of span)
        pairs_msh_avail.csv          (pairs_msh.csv + overlap_days_data, overlap_yr_data)
Source: EarthScope MUSTANG `percent_availability` metric (daily, per channel). The
fdsnws availability service and the station-service includeavailability option were
retired (HTTP 404 / 410 on 2026-11-15), so MUSTANG is the remaining public source.
MUSTANG only has days it has processed; treat a missing day as unknown-or-absent.
Vertical seismometer channels only (EHZ, HHZ, BHZ, SHZ); strong-motion HN? excluded.
A station-day counts if any vertical channel has >= MIN_PCT % availability.
"""
import io, sys
import numpy as np, pandas as pd, requests

URL = "https://service.earthscope.org/mustang/measurements/1/query"
CHA = "EHZ,HHZ,BHZ,SHZ"
MIN_PCT = 90.0

def daily(net, sta):
    r = requests.get(URL, params=dict(metric="percent_availability", net=net, sta=sta,
                                      cha=CHA, format="text"), timeout=600)
    r.raise_for_status()
    txt = "\n".join(l for l in r.text.splitlines()[1:] if l.strip())
    if txt.count("\n") < 1:
        return pd.DataFrame()
    df = pd.read_csv(io.StringIO(txt))
    out = pd.DataFrame({"sta": f"{net}.{sta}",
                        "cha": df["target"].str.split(".").str[3],
                        "loc": df["target"].str.split(".").str[2],
                        "date": pd.to_datetime(df["start"]).dt.normalize(),
                        "pct": df["value"].astype(float)})
    return out.groupby(["sta", "loc", "cha", "date"], as_index=False).pct.max()

if __name__ == "__main__":
    pairs = pd.read_csv("pairs_msh.csv")
    stas = sorted(set(pairs.sta1) | set(pairs.sta2))
    alld, days, summ = [], {}, []
    for ns in stas:
        df = daily(*ns.split("."))
        if df.empty:
            print(ns, "NO DATA", file=sys.stderr); days[ns] = set(); continue
        alld.append(df)
        good = df[df.pct >= MIN_PCT]
        days[ns] = set(good.date)
        if not days[ns]:
            print(ns, f"no day >= {MIN_PCT} % (max {df.pct.max():.1f} %, {len(df)} channel-days)",
                  file=sys.stderr)
            summ.append(dict(sta=ns, channels=",".join(sorted(df.cha.unique())),
                             days_with_data=0, years_with_data=0.0)); continue
        d = pd.DatetimeIndex(sorted(days[ns]))
        span = (d[-1] - d[0]).days + 1
        summ.append(dict(sta=ns, channels=",".join(sorted(df.cha.unique())),
                         first=d[0].date(), last=d[-1].date(), days_with_data=len(d),
                         years_with_data=round(len(d) / 365.25, 1),
                         fraction_of_span=round(len(d) / span, 3)))
        print(summ[-1])
    pd.concat(alld).to_csv("availability_daily_msh.csv", index=False)
    pd.DataFrame(summ).to_csv("availability_summary_msh.csv", index=False)
    ov = [len(days[a] & days[b]) for a, b in zip(pairs.sta1, pairs.sta2)]
    pairs["overlap_days_data"] = ov
    pairs["overlap_yr_data"] = (np.array(ov) / 365.25).round(1)
    pairs.to_csv("pairs_msh_avail.csv", index=False)
