import os
import pickle

import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Column order the scaler and model were trained on (Boston Housing dataset).
FEATURES = ["CRIM", "ZN", "INDUS", "CHAS", "NOX", "RM", "Age",
            "DIS", "RAD", "TAX", "PTRATIO", "B", "LSTAT"]

## Load the model
with open(os.path.join(BASE_DIR, "regmodel.pkl"), "rb") as f:
    regmodel = pickle.load(f)
with open(os.path.join(BASE_DIR, "scaling.pkl"), "rb") as f:
    scalar = pickle.load(f)


def predict_price(values):
    frame = pd.DataFrame([values], columns=scalar.feature_names_in_, dtype=float)
    new_data = scalar.transform(frame)
    return float(regmodel.predict(new_data)[0])


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/predict_api", methods=["POST"])
def predict_api():
    data = request.get_json(force=True)["data"]
    try:
        values = [data[name] for name in FEATURES]
    except KeyError as e:
        return jsonify({"error": f"missing feature {e}"}), 400
    return jsonify(predict_price(values))


@app.route("/predict", methods=["POST"])
def predict():
    try:
        values = [float(request.form[name]) for name in FEATURES]
    except (KeyError, ValueError):
        return render_template("home.html", prediction_text="Please enter a number in every field."), 400
    output = predict_price(values)
    return render_template("home.html", prediction_text="The predicted house price is ${:,.0f}".format(output * 1000))


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
