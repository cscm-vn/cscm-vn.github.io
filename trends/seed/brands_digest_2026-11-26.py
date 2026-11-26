# Tuần 26/11/2026: không có tin mới đã kiểm chứng; dọn mục hết hạn.
import json
from datetime import date, timedelta
TODAY = "2026-11-26"
p = "trends/data/brands.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = TODAY
cut = (date.fromisoformat(TODAY) - timedelta(days=90)).isoformat()
d["emerging"] = [e for e in d.get("emerging", []) if e["date"] >= cut]
c60 = (date.fromisoformat(TODAY) - timedelta(days=60)).isoformat()
for b in d["brands"]:
    if b.get("digest") and b["digest"]["date"] < c60: del b["digest"]
for v in d["cats"].values():
    if v.get("digest") and v["digest"]["date"] < c60: del v["digest"]
d["emerging"].sort(key=lambda e: e["date"], reverse=True)
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
