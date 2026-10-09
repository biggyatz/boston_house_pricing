// Hedonic price model exported by train_property_model.py.
// log(price) = intercept + sum(coef * feature); features mirror design() in Python.
const AANA_SQFT = 342.25;
function features(model, x) {
  const f = {};
  const house = x.type === "House" ? 1 : 0;
  f.house = house;
  f.log_area = Math.log(x.area_aana);
  f.house_log_area = house * f.log_area;
  const road = x.road_ft == null ? null : Math.min(40, Math.max(4, x.road_ft));
  f.road_missing = road == null ? 1 : 0;
  f.log_road = Math.log(road == null ? 13 : road);
  const st = x.storeys == null ? null : Math.min(6, Math.max(1, x.storeys));
  f.storey_missing = house && st == null ? 1 : 0;
  f.storeys = house * (st == null ? 2.5 : st);
  f["d=" + x.district] = 1;
  if (x.locality) f["l=" + x.locality + " | " + x.district] = 1;
  f["y=" + (x.year || model.latest_year)] = 1;
  return f;
}
function predictPrice(model, x) {
  const f = features(model, x);
  let z = model.intercept;
  for (const [k, v] of Object.entries(f)) if (k in model.coef) z += model.coef[k] * v;
  return {
    price: Math.exp(z),
    low: Math.exp(z + model.resid_q["0.1"]), high: Math.exp(z + model.resid_q["0.9"]),
    q1: Math.exp(z + model.resid_q["0.25"]), q3: Math.exp(z + model.resid_q["0.75"]),
  };
}
if (typeof module !== "undefined") module.exports = { predictPrice, features };
