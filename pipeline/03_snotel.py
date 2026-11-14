"""Daily SNOTEL forcing -> data/forcing_<site>.csv (date, swe_m, precip_m, tair_c)
for analysis/phase_test.py. Uses the NRCS report-generator CSV endpoint.
VERIFY the URL pattern on first run (written from the public report-generator
format; not testable from the sandbox). Station IDs confirmed in NRCS listings:
June Lake 553, Swift Creek 1012 (St. Helens S flank); Potato Hill 702 (Adams N);
Surprise Lakes 804 (Indian Heaven). Add Sheep Canyon / Pepper Creek by ID.
Avoid Spirit Lake SNOTEL as a flank proxy (windswept, rain-shadowed).
"""
import io, pathlib, sys
import pandas as pd, requests

STATIONS = {"june_lake": "553:WA:SNTL", "swift_creek": "1012:WA:SNTL",
            "potato_hill": "702:WA:SNTL", "surprise_lakes": "804:WA:SNTL"}
BASE = ("https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/"
        "customSingleStationReport/daily/{trip}%7Cid=%22%22%7Cname/{start},{end}/"
        "WTEQ::value,PREC::value,TAVG::value")

def fetch(trip, start="1997-10-01", end="2026-09-30"):
    r = requests.get(BASE.format(trip=trip, start=start, end=end), timeout=120)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), comment="#")
    df.columns = ["date", "swe_in", "prec_cum_in", "tavg_f"]
    df["date"] = pd.to_datetime(df["date"])
    out = pd.DataFrame({"date": df["date"],
                        "swe_m": df["swe_in"] * 0.0254,
                        # PREC is water-year accumulated; daily = positive increments
                        "precip_m": df["prec_cum_in"].diff().clip(lower=0) * 0.0254,
                        "tair_c": (df["tavg_f"] - 32) * 5 / 9})
    return out

if __name__ == "__main__":
    pathlib.Path("../data").mkdir(exist_ok=True)
    for name, trip in STATIONS.items():
        try:
            df = fetch(trip)
            df.to_csv(f"../data/forcing_{name}.csv", index=False)
            print(name, len(df), df.date.min().date(), df.date.max().date(),
                  "peak SWE median (m):", round(df.groupby(df.date.dt.year).swe_m.max().median(), 2))
        except Exception as e:
            print(name, "FAILED:", e, file=sys.stderr)
