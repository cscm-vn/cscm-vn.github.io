#!/usr/bin/env python3
"""Build a fully static copy of the dashboard into ./site (for GitHub Pages / Netlify / any static host)."""
import os, shutil, json
from app import app
BASE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(BASE, "site")
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(os.path.join(OUT, "history")); os.makedirs(os.path.join(OUT, "static"))
c = app.test_client()
shutil.copy(os.path.join(BASE, "static", "index.html"), OUT)
shutil.copy(os.path.join(BASE, "static", "chart.umd.min.js"), os.path.join(OUT, "static"))
d = c.get("/api/prices").get_json()
json.dump(d, open(os.path.join(OUT, "prices.json"), "w"), ensure_ascii=False)
for it in d["items"]:
    open(os.path.join(OUT, "history", it["id"] + ".json"), "wb").write(c.get(f"/api/history/{it['id']}").data)
open(os.path.join(OUT, "bang-gia.csv"), "wb").write(c.get("/api/export.csv").data)
open(os.path.join(OUT, "lich-su-gia.csv"), "wb").write(c.get("/api/history.csv").data)
open(os.path.join(OUT, "bang-gia.xlsx"), "wb").write(c.get("/api/export.xlsx").data)
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("static site ->", OUT, len(d["items"]), "items")
