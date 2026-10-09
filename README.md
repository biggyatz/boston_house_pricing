# Nepal Property Price Estimator

**Live app:** <https://biggyatz.github.io/boston_house_pricing/>

Estimate the asking price of a house or plot of land anywhere in Nepal (Kathmandu, Lalitpur, Bhaktapur, Pokhara, Chitwan, the Terai and more) from **1,923 real listings**. Enter the type, district, locality, land area (ropani-aana-paisa-dam, or bigha-kattha-dhur in the Terai), road width and storeys. You get an estimate with a likely range, the price per aana, the most similar listings on the market (linked to their source), and a ranking of areas by price per aana.

The app is a static page on GitHub Pages: the model runs in the browser, with no server and no cost.

> This repository started as a Boston house-price regression. That original project is preserved in [`legacy-boston/`](legacy-boston/).

## Data

| Source | Listings used | Period | How it was collected |
| --- | --- | --- | --- |
| [99aana.com](https://99aana.com) | 1,742 | 2021–2026 | Property pages from the site's sitemap (`robots.txt`: allow all) |
| [hamrobazaar.com](https://hamrobazaar.com) | 181 | 2025–2026 | Search and listing pages (`/search/product`, `/detail/`, both allowed in `robots.txt`) |

* Collected in October 2026 at roughly one request per second.
* Only property attributes are kept: type, price, address, land area, road, storeys, listing date and source URL. Phone numbers and seller names are never stored.
* These are **asking prices**, which usually exceed final sale prices. Treat estimates as market-listing levels, not a valuation.

Cleaning (`data/clean_property.py`):
* Nepali prices are parsed (`1 crore 50 lakh`, `Rs 2,20,00,000`, `18 lakh per aana`, and `270` meaning 270 lakh).
* Land units are converted to aana (1 ropani = 16 aana = 5,476 sq ft; 1 dhur = 182.25 sq ft). Hamrobazar's "Aana/Dhur" field is read as dhur in Terai districts.
* District and locality come from the address or title, with spelling variants merged (Buddhanilkantha → Budhanilkantha).
* Price-per-aana outliers more than 5× from their district median are dropped.

## Model

A hedonic regression on log(price) with ridge regularisation:

`log(price) = district + locality + type + type × log(area) + log(road width) + storeys + listing year`

* Localities with at least 4 listings get their own effect, shrunk toward the district by the ridge penalty; others use the district level.
* Year effects let older listings inform the model while estimates are made at 2026 levels.

| 5-fold cross-validation | Ridge (deployed) | Gradient boosting |
| --- | --- | --- |
| R² (log price) | 0.746 | 0.735 |
| Median absolute error | 24.2% | 23.2% |
| Within ±25% | 51.6% | 52.3% |

The regression is kept because it is as accurate as gradient boosting here, every effect is explainable, and it behaves sensibly for areas with few listings. `web/predict.js` reproduces the Python model exactly (max relative difference ~1e-14 over all listings). The likely range shown in the app is the 10th–90th percentile of cross-validated errors.

## Repository layout

| Path | What it is |
| --- | --- |
| `web/` | The app: `index.html`, `app.js`, `predict.js`, `style.css`, plus `model.json` and `listings.json` |
| `data/crawl_99aana.py`, `data/crawl_hamrobazar*.js` | Polite crawlers (robots.txt-compliant, rate-limited, no personal data) |
| `data/clean_property.py`, `data/nepal_units.py` | Parsing of Nepali prices, land units, addresses and years |
| `data/train_property_model.py` | Model training and cross-validation |
| `data/export_property_web.py` | Writes `web/model.json` and `web/listings.json` |
| `data/property_listings.csv` | The cleaned dataset |
| `legacy-boston/` | The original Boston Housing project (Flask, Docker) |

## Refreshing the data

```bash
cd data
python crawl_99aana.py                       # needs urls_99aana.txt from the 99aana property sitemaps
node crawl_hamrobazar.js '/detail/for-sale-(house|land)/' raw_hamrobazar_realestate.jsonl "house sale kathmandu" ...
node crawl_hamrobazar_details.js raw_hamrobazar_realestate.jsonl raw_hamrobazar_re_details.jsonl
python clean_property.py && python train_property_model.py && python export_property_web.py ../web
```

Pushing to `main` republishes the site via `.github/workflows/pages.yml`.
