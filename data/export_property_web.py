"""Write web/model.json and web/listings.json for the property app."""
import json, re, sys
import pandas as pd
out_dir = sys.argv[1]
model = json.load(open("property_model.json"))
df = pd.read_csv("property_model_rows.csv")
rows = [{"title": r.title[:90], "type": r.type, "locality": r.locality if isinstance(r.locality, str) else None, "district": r.district,
         "price": int(r.price_npr), "area": round(float(r.area_aana), 3), "url": r.url, "source": r.source, "year": int(r.year)}
        for r in df.itertuples()]
json.dump(model, open(f"{out_dir}/model.json", "w"), separators=(",", ":"))
json.dump(rows, open(f"{out_dir}/listings.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("model + listings", len(rows))
