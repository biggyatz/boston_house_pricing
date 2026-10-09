"""Export the trained scaler + linear regression to web/model.json.

The GitHub Pages version of the app (web/) runs the exact same maths in the
browser: price = intercept + sum(coef * (x - mean) / scale).

    python export_web_model.py
"""
import json
import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "regmodel.pkl"), "rb") as f:
    model = pickle.load(f)
with open(os.path.join(BASE_DIR, "scaling.pkl"), "rb") as f:
    scaler = pickle.load(f)

export = {
    "features": list(scaler.feature_names_in_),
    "mean": scaler.mean_.tolist(),
    "scale": scaler.scale_.tolist(),
    "coef": model.coef_.ravel().tolist(),
    "intercept": float(model.intercept_),
}
with open(os.path.join(BASE_DIR, "web", "model.json"), "w") as f:
    json.dump(export, f, indent=1)
print("Wrote web/model.json")
