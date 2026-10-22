"""Nhập bảng đơn giá nguyên tắc HĐ (TSV xuất từ Excel) vào data/registry/contract_baselines.json.
Dùng: python dieu_chinh/import_tsv.py FILE.tsv --id tong-thau-2026 --name "..." --version 2026-10-22 --effective 2026-10-22
Cột bắt buộc: MIỀN, NHÓM, MÃ, MÔ TẢ CHI TIẾT, ĐƠN VỊ, TỶ TRỌNG, NGƯỠNG CTD, NGƯỠNG NTC, ĐƠN GIÁ CTD, ĐƠN GIÁ NTC.
Số kiểu VN: '1.350.000', '0,25%', '±3%'. Ô trống = null (không bịa). Hợp đồng cùng id + version sẽ được thay thế; version khác được thêm."""
import argparse, csv, json, os, re, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data", "registry", "contract_baselines.json")
N = lambda s: unicodedata.normalize("NFC", (s or "").strip())
def num(s):
    s = N(s).replace("±", "").replace("%", "").replace(" ", "")
    if not s: return None
    if "," in s: s = s.replace(".", "").replace(",", ".")   # 0,25 -> 0.25
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s): s = s.replace(".", "")  # 1.350.000 -> 1350000
    return float(s)
REGION = {"miền bắc": "bac", "miền nam": "nam", "miền trung": "trung"}
def parse(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig"), delimiter="\t"))
    out = []
    for r in rows:
        r = {N(k).upper(): v for k, v in r.items()}
        if not N(r.get("MÃ")): continue
        out.append(dict(region=REGION[N(r["MIỀN"]).lower()], group=N(r["NHÓM"]), code=N(r["MÃ"]), desc=N(r["MÔ TẢ CHI TIẾT"]), unit=N(r["ĐƠN VỊ"]),
                        weight_pct=num(r.get("TỶ TRỌNG")), thr_ctd_pct=num(r.get("NGƯỠNG CTD")), thr_ntc_pct=num(r.get("NGƯỠNG NTC")),
                        ctd=num(r.get("ĐƠN GIÁ CTD")), ntc=num(r.get("ĐƠN GIÁ NTC"))))
    return out
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("tsv"); ap.add_argument("--id", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--version", required=True); ap.add_argument("--effective", required=True); ap.add_argument("--note", default="")
    a = ap.parse_args()
    reg = json.load(open(REG, encoding="utf-8")) if os.path.exists(REG) else {"schema_version": 1, "contracts": []}
    c = dict(id=a.id, name=a.name, version=a.version, effective_date=a.effective, currency="VND", note=a.note,
             bases={"CTD": "Đơn giá nguyên tắc CTD", "NTC": "Đơn giá nguyên tắc NTC"},
             source_file=os.path.basename(a.tsv), items=parse(a.tsv))
    reg["contracts"] = [x for x in reg["contracts"] if not (x["id"] == a.id and x["version"] == a.version)] + [c]
    reg["contracts"].sort(key=lambda x: (x["id"], x["version"]))
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1); open(REG, "a").write("\n")
    print(f"{a.id} v{a.version}: {len(c['items'])} dòng → {REG}")
