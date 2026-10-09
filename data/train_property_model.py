"""Hedonic price model for Nepal property listings -> model.json for the web app.

log(price) = district + locality (ridge-shrunk) + type + type x log(area) + road width
             + storeys + listing year
Compared against gradient boosting with 5-fold CV; the linear model is exported
when it is competitive because it is transparent and runs in a few lines of JS.
"""
import json, sys
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold, cross_val_predict

df = pd.read_csv("property.csv")
df = df[(df.price_npr > 5e5) & (df.area_aana >= 0.5) & (df.area_aana <= 400)].copy()
# Drop absurd price-per-aana outliers within each district/type (data entry errors, wrong units).
lp = np.log(df.price_per_aana)
grp = df.groupby(["district", "type"])[["price_per_aana"]].transform(lambda s: np.log(s).median())["price_per_aana"]
df = df[(lp - grp).abs() < np.log(5)].copy()
df["district"] = df.district.fillna("Other")
df["year"] = pd.to_datetime(df.listed, errors="coerce").dt.year
df = df.dropna(subset=["year"])
MIN_LOC = 4
loc_counts = df.locality.value_counts()
df["loc"] = np.where(df.locality.isin(loc_counts[loc_counts >= MIN_LOC].index), df.locality + " | " + df.district, "")

def design(d, cols=None):
    house = (d.type == "House").astype(float)
    log_area = np.log(d.area_aana)
    road = d.road_ft.clip(4, 40)
    st = d.floors.clip(1, 6)
    f = {"house": house, "log_area": log_area, "house_log_area": house * log_area,
         "road_missing": road.isna().astype(float), "log_road": np.log(road.fillna(13)),
         "storey_missing": (house * st.isna()).astype(float), "storeys": house * st.fillna(2.5)}
    for v in sorted(d.district.unique()): f["d=" + v] = (d.district == v).astype(float)
    for v in sorted(set(d["loc"]) - {""}): f["l=" + v] = (d["loc"] == v).astype(float)
    for v in sorted(d.year.unique()): f["y=" + str(int(v))] = (d.year == v).astype(float)
    X = pd.DataFrame(f, index=d.index)
    return X if cols is None else X.reindex(columns=cols, fill_value=0.0)

X, y = design(df), np.log(df.price_npr.values)
cv = KFold(5, shuffle=True, random_state=42)
ridge = RidgeCV(alphas=np.logspace(-2, 2, 20))
p_lin = cross_val_predict(ridge, X, y, cv=cv)
gb = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, min_samples_leaf=15, random_state=0)
p_gb = cross_val_predict(gb, X, y, cv=cv)
def report(p):
    err = np.exp(p) / np.exp(y) - 1
    return {"r2_log": round(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum(), 3),
            "median_abs_pct_err": round(float(np.median(np.abs(err))) * 100, 1),
            "within_25pct": round(float((np.abs(err) < 0.25).mean()) * 100, 1)}
print("rows", len(df), "features", X.shape[1])
print("ridge", report(p_lin)); print("gboost", report(p_gb))

ridge.fit(X, y)
resid = y - p_lin
coef = dict(zip(X.columns, ridge.coef_.tolist()))
latest = int(df.year.max())
model = {
    "intercept": float(ridge.intercept_), "coef": coef, "alpha": float(ridge.alpha_), "latest_year": latest,
    "resid_q": {q: float(np.quantile(resid, q)) for q in (0.1, 0.25, 0.75, 0.9)},
    "cv": report(p_lin), "cv_gboost": report(p_gb), "n": int(len(df)),
    "sources": df.source.value_counts().to_dict(),
    "years": {int(k): int(v) for k, v in df.year.value_counts().sort_index().items()},
    "districts": sorted(df.district.unique()),
    "localities": [{"name": l.split(" | ")[0], "district": l.split(" | ")[1], "n": int((df["loc"] == l).sum())}
                   for l in sorted(set(df["loc"]) - {""})],
}
json.dump(model, open("property_model.json", "w"), indent=1)
df.to_csv("property_model_rows.csv", index=False)
print("alpha", ridge.alpha_, "localities", len(model["localities"]), "latest", latest)
