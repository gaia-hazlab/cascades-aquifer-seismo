"""Target boxes. Centres are approximate summit / feature coordinates;
radius ~0.3 deg (~30 km). Edit freely."""
TARGETS = {
    # WA: Karlstrom's 'north of the Columbia Gorge' aquifer
    "msh":            dict(lat=46.191, lon=-122.195, r=0.30, label="Mount St. Helens"),
    "adams":          dict(lat=46.202, lon=-121.490, r=0.30, label="Mount Adams"),
    "indian_heaven":  dict(lat=45.930, lon=-121.820, r=0.25, label="Indian Heaven (between)"),
    # OR: Karlstrom et al. 2025 PNAS study area
    "santiam_pass":   dict(lat=44.420, lon=-121.870, r=0.30, label="Santiam Pass / McKenzie headwaters"),
    "three_sisters":  dict(lat=44.149, lon=-121.783, r=0.30, label="Three Sisters"),
    # CA
    "shasta":         dict(lat=41.409, lon=-122.193, r=0.35, label="Mount Shasta"),
    "medicine_lake":  dict(lat=41.580, lon=-121.600, r=0.35, label="Medicine Lake Volcano (Fall River recharge)"),
    "lassen":         dict(lat=40.488, lon=-121.505, r=0.30, label="Lassen Peak (Hat Creek)"),
}

def bbox(t):
    return [t["lon"] - t["r"], t["lat"] - t["r"], t["lon"] + t["r"], t["lat"] + t["r"]]
