// Same maths as app.py: StandardScaler followed by LinearRegression.
// Returns the predicted median value in $1000s.
function predictPrice(model, values) {
  let y = model.intercept;
  for (let i = 0; i < model.coef.length; i++) {
    y += model.coef[i] * (values[i] - model.mean[i]) / model.scale[i];
  }
  return y;
}

if (typeof module !== "undefined") module.exports = { predictPrice };
