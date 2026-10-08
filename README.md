# Boston House Pricing

A linear-regression model that predicts the median value of a Boston home
from 13 neighbourhood features, served as a Flask web app with a JSON API.

| Metric (test set) | Value |
| --- | --- |
| R² | 0.711 |
| Adjusted R² | 0.684 |
| MAE | 3.16 ($k) |
| RMSE | 4.64 ($k) |

## Features the model expects

`CRIM` crime rate · `ZN` residential land zoned for large lots · `INDUS`
non-retail business acres · `CHAS` borders Charles River (1/0) · `NOX` nitric
oxide concentration · `RM` average rooms · `AGE` pre-1940 homes (%) · `DIS`
distance to employment centres · `RAD` highway access index · `TAX` property
tax rate · `PTRATIO` pupil–teacher ratio · `B` demographic index · `LSTAT`
lower-status population (%).

## Project layout

| Path | What it is |
| --- | --- |
| `app.py` | Flask app: web form (`/`, `/predict`), JSON API (`/predict_api`), health check (`/health`) |
| `regmodel.pkl`, `scaling.pkl` | Trained `LinearRegression` and `StandardScaler` (scikit-learn 1.4.2) |
| `linear regression.ipynb` | EDA, training and evaluation |
| `templates/home.html` | Input form |
| `Dockerfile`, `render.yaml`, `Procfile` | Deployment config |

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py                         # http://localhost:5000
```

Or with Docker:

```bash
docker build -t boston-house-pricing .
docker run -p 8000:8000 boston-house-pricing   # http://localhost:8000
```

### API

```bash
curl -X POST http://localhost:5000/predict_api -H 'Content-Type: application/json' -d '{
  "data": {"CRIM": 0.00632, "ZN": 18, "INDUS": 2.31, "CHAS": 0, "NOX": 0.538, "RM": 6.575,
           "Age": 65.2, "DIS": 4.09, "RAD": 1, "TAX": 296, "PTRATIO": 15.3, "B": 396.9, "LSTAT": 4.98}
}'
# 30.086...  (price in $1000s)
```

To retrain, install `requirements-dev.txt` and run the notebook.

## Deploy

This app was originally on Heroku, whose free tier ended in November 2022.
It now deploys on **Render's free plan** via the included `render.yaml`:

1. Sign in at <https://dashboard.render.com> with GitHub.
2. **New → Blueprint** → select this repository → **Apply**.
3. Render builds the Dockerfile and gives you a `https://boston-house-pricing-xxxx.onrender.com` URL.

Free Render services sleep after 15 minutes idle; the first request after that
takes ~30–60 s. The same Dockerfile runs unchanged on Railway, Fly.io, Google
Cloud Run or Hugging Face Spaces (Docker SDK, port 8000 → set `PORT=7860`).
