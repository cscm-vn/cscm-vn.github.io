#!/usr/bin/env python3
"""Luật & chính sách mới liên quan Masterise (hop-dong.html#chinh-sach + trang chủ).
Real feeds only: Google News RSS (vi) + official/press RSS. Dedup by normalized title, 30-day window.
Each item gets a rule-based score (relevance to Masterise + recency/dynamics) and a one-line reason built ONLY from
matched keywords in the title/summary (no invented facts). Writes trends/data/policy-feed.json. Never raises."""
import json, os, re, hashlib, unicodedata, html, datetime as dt, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"); OUT = os.path.join(D, "policy-feed.json")
TZ = dt.timezone(dt.timedelta(hours=7)); KEEP_DAYS = 30
GN = "https://news.google.com/rss/search?q={q}&hl=vi&gl=VN&ceid=VN:vi"
Q = [  # Google News queries (topic hint only; topics are re-derived from text)
 "nghị định Luật Đất đai when:14d", "bảng giá đất Hà Nội TP.HCM when:14d", "thông tư Bộ Xây dựng mới when:14d", "Luật Xây dựng 2025 nghị định hướng dẫn when:14d",
 "Luật Nhà ở chung cư nghị định when:14d", "thời hạn sở hữu chung cư when:30d", "Luật Kinh doanh bất động sản nghị định when:14d", "nhà ở xã hội quy định chủ đầu tư when:14d",
 "giấy phép xây dựng quy định mới when:14d", "phòng cháy chữa cháy chung cư quy định when:14d", "Luật Địa chất và Khoáng sản nghị định when:14d",
 "khai thác cát sỏi vật liệu xây dựng quy định when:14d", "mỏ đá mỏ đất san lấp cấp phép when:14d", "thuế chuyển nhượng bất động sản dự thảo when:14d",
 "dự thảo nghị định bất động sản lấy ý kiến when:14d", "Masterise Homes when:30d",
 "site:chinhphu.vn bất động sản OR đất đai OR xây dựng when:14d", "site:thuvienphapluat.vn đất đai OR nhà ở OR xây dựng when:14d",
 "site:moc.gov.vn when:30d", "site:xaydung.gov.vn when:30d", "site:cafeland.vn chính sách when:14d", "site:baochinhphu.vn nhà ở OR đất đai when:14d"]
RSS = [("Chinhphu.vn – Chính sách mới", "https://xaydungchinhsach.chinhphu.vn/chinh-sach-moi.rss"), ("Báo Chính phủ – Chính sách mới", "https://baochinhphu.vn/chinh-sach-moi.rss"),
       ("VnExpress – Pháp luật", "https://vnexpress.net/rss/phap-luat.rss"), ("VnExpress – Bất động sản", "https://vnexpress.net/rss/bat-dong-san.rss")]
def strip(s): return unicodedata.normalize("NFD", (s or "").lower().replace("đ", "d")).encode("ascii", "ignore").decode()
# topic -> (label, accent-free keywords). An item must match ≥1 topic AND ≥1 legal/policy word to be kept.
TOPIC = {"dat-dai": ("Đất đai", ["dat dai", "gia dat", "bang gia dat", "quyen su dung dat", "giao dat", "thu hoi dat", "tien su dung dat", "chuyen muc dich su dung dat", "dau gia dat", "so do", "tien thue dat"]),
 "nha-o": ("Nhà ở & chung cư", ["luat nha o", "chung cu", "nha o thuong mai", "nha o xa hoi", "so huu nha", "thoi han so huu", "can ho", "nha chung cu", "cai tao chung cu"]),
 "kd-bds": ("Kinh doanh BĐS", ["kinh doanh bat dong san", "bat dong san", "nha o hinh thanh trong tuong lai", "san giao dich", "chuyen nhuong du an", "ban nha o", "moi gioi"]),
 "xay-dung": ("Xây dựng", ["luat xay dung", "bo xay dung", "giay phep xay dung", "cap phep xay dung", "quy chuan", "tieu chuan xay dung", "quy hoach", "chi phi dau tu xay dung", "hop dong xay dung", "cong trinh xay dung", "dinh muc xay dung"]),
 "pccc": ("PCCC", ["phong chay", "chua chay", "pccc", "cuu nan cuu ho"]),
 "khoang-san": ("Khoáng sản & VLXD", ["khoang san", "cat song", "cat san lap", "cat xay dung", "mo cat", "mo da", "da xay dung", "dat san lap", "mo dat", "set gach", "vat lieu xay dung", "dia chat"]),
 "thue": ("Thuế BĐS", ["thue chuyen nhuong", "thue bat dong san", "thue thu nhap ca nhan tu chuyen nhuong", "thue nha", "thue su dung dat", "thue doi voi nguoi so huu nhieu nha", "le phi truoc ba"])}
LEGAL = ["luat", "nghi dinh", "thong tu", "nghi quyet", "quyet dinh", "du thao", "quy dinh", "chinh sach", "huong dan", "sua doi", "hieu luc", "ban hanh", "cong van", "chi thi", "bang gia", "cap phep", "lay y kien", "quy chuan"]
# relevance weights (Masterise: luxury condo developer, HN & HCMC) – reason text is fixed per rule
REL = [  # (keywords, points, reason)
 (["masterise", "masteri", "lumiere", "grand marina", "the global city", "masterise homes", "ocean park", "vinhomes smart city masteri"], 45, "Nhắc trực tiếp Masterise / dự án Masterise"),
 (["thoi han so huu", "so huu chung cu", "nien han chung cu"], 22, "Thời hạn sở hữu chung cư – ảnh hưởng sản phẩm căn hộ"),
 (["bang gia dat", "gia dat", "tien su dung dat", "he so dieu chinh gia dat", "tien thue dat"], 22, "Giá đất / tiền sử dụng đất – tác động chi phí quỹ đất & giá bán"),
 (["quyen su dung dat", "giao dat", "cho thue dat", "thu hoi dat", "chuyen muc dich", "dau gia dat", "so do", "giay chung nhan"], 16, "Quyền sử dụng đất / giao đất / cấp sổ – pháp lý dự án"),
 (["chung cu", "can ho", "nha o thuong mai"], 15, "Liên quan chung cư / nhà ở thương mại – sản phẩm chính"),
 (["kinh doanh bat dong san", "hinh thanh trong tuong lai", "chuyen nhuong du an", "mo ban", "dat coc"], 14, "Luật Kinh doanh BĐS – điều kiện mở bán, chuyển nhượng"),
 (["giay phep xay dung", "cap phep xay dung", "tham dinh thiet ke", "luat xay dung", "nghiem thu"], 13, "Cấp phép / thẩm định xây dựng – tiến độ dự án"),
 (["phong chay", "chua chay", "pccc"], 13, "PCCC – điều kiện nghiệm thu, vận hành chung cư"),
 (["cat xay dung", "cat san lap", "cat song", "mo cat", "khai thac cat", "cat soi", "da xay dung", "mo da", "dat san lap", "khoang san", "vat lieu xay dung", "set gach"], 12, "Nguồn cung khoáng sản/VLXD (cát, đá, đất) – giá & tiến độ thi công"),
 (["thue chuyen nhuong", "thue thu nhap ca nhan", "thue su dung dat", "thue tai san", "thue bat dong san", "thue nha", "le phi truoc ba"], 11, "Thuế/phí BĐS – tác động cầu & giá bán"),
 (["nha o xa hoi", "20% quy dat"], 11, "Nghĩa vụ nhà ở xã hội của chủ đầu tư"),
 (["ha noi"], 7, "Áp dụng tại Hà Nội (thị trường dự án)"), (["tp.hcm", "tp hcm", "ho chi minh", "thanh pho ho chi minh", "sai gon"], 7, "Áp dụng tại TP.HCM (thị trường dự án)"),
 (["quy hoach"], 6, "Quy hoạch – ảnh hưởng quỹ đất"), (["hop dong xay dung", "chi phi dau tu xay dung", "dinh muc xay dung", "chi so gia xay dung"], 6, "Quản lý chi phí / HĐ xây dựng")]
DYN = [  # recency/dynamics (max one per group by order)
 (["co hieu luc tu", "hieu luc tu ngay", "chinh thuc co hieu luc", "bat dau co hieu luc", "tu ngay 1/", "tu 1/"], 14, "sắp/đã có hiệu lực"),
 (["ban hanh", "vua ky", "da ky", "thong qua", "chinh thuc"], 12, "văn bản mới ban hành/thông qua"),
 (["du thao", "lay y kien", "gop y"], 10, "dự thảo đang lấy ý kiến"),
 (["sua doi", "bo sung", "thay the", "moi nhat", "quy dinh moi"], 7, "thay đổi quy định"),]
DOC = [(r"\bnghi dinh\b|\bnd\s?\d", 8, "Nghị định"), (r"\bthong tu\b", 7, "Thông tư"), (r"\bluat\b", 8, "Luật"), (r"\bnghi quyet\b", 7, "Nghị quyết"), (r"\bquyet dinh\b|\bcong van\b|\bchi thi\b", 4, "QĐ/CV")]
THEME = {1: "Thời hạn sở hữu chung cư", 2: "Giá đất & tiền sử dụng đất", 3: "Quyền sử dụng đất & giao đất", 4: "Chung cư & nhà ở thương mại", 5: "Kinh doanh BĐS (mở bán, chuyển nhượng)",
 6: "Cấp phép & thẩm định xây dựng", 7: "Phòng cháy chữa cháy", 8: "Khoáng sản & VLXD (cát, đá, đất)", 9: "Thuế & phí BĐS", 10: "Nhà ở xã hội", 11: "Hà Nội", 12: "TP.HCM", 13: "Quy hoạch", 14: "Chi phí & HĐ xây dựng"}
THEME_PREF = {"nha-o": [1, 10, 4], "dat-dai": [2, 3, 13], "kd-bds": [5, 10], "xay-dung": [6, 14, 13], "pccc": [7], "khoang-san": [8], "thue": [9]}  # chủ đề con ưu tiên theo chủ đề chính
GENERIC_LAW = ["luat sua doi", "luat (sua doi)", "luat nay", "luat moi", "luat hoa", "luat chuyen nganh", "luat su", "luat le", "phap luat", "du luat", "luat gop"]
def side_law(t):
    """Dự luật gộp: luật được nhắc ĐẦU TIÊN trong tiêu đề không thuộc nhóm liên quan (vd. 'Luật Quản lý vũ khí…, Luật PCCC') → luật liên quan chỉ là phần phụ."""
    pos = [m.start() for m in re.finditer(r"(?<![a-z])luat ", t) if not any(t.startswith(g, m.start() - (2 if g.startswith("ph") or g.startswith("du") else 0)) for g in GENERIC_LAW)]
    if not pos: return False
    first = pos[0]; return not any(t.startswith(k, first) for k, _ in LAWS) and any(has(t[first:], k) for k, _ in LAWS)
def has(t, k): return re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", t) is not None
def score(x, now):
    t = strip(x["title"] + " " + x.get("summary", "")); rel, why, tags = 0, [], []
    for ks, p, r in REL:
        if any(has(t, k) for k in ks): rel += p; why.append(r)
    side = side_law(strip(x["title"]))
    if side: rel = round(rel * 0.4)  # phạt: lĩnh vực liên quan chỉ là phần phụ của dự luật gộp
    dyn, dn = 0, []
    for ks, p, r in DYN:
        if any(has(t, k) for k in ks): dyn += p; dn.append(r)
    for rx, p, r in DOC:
        if re.search(rx, t): dyn += p; tags.append(r); break
    age = max(0.0, (now - dt.datetime.fromisoformat(x["published"] or x["found"])).total_seconds() / 86400)
    rec = max(0, round(20 * (1 - age / KEEP_DAYS)))  # 20 hôm nay → 0 ở ngày 30
    s = min(100, min(rel, 60) + min(dyn, 25) + rec // 1)
    reason = "; ".join(why[:2]) or "Chính sách ngành BĐS/xây dựng"
    if dn: reason += " · " + ", ".join(dn[:2])
    if side: reason += " · (chỉ là phần phụ của dự luật gộp – giảm điểm)"
    return s, reason, dict(rel=min(rel, 60), dyn=min(dyn, 25), rec=rec)
LAWS = [("luat dat dai", "Luật Đất đai"), ("luat nha o", "Luật Nhà ở"), ("luat kinh doanh bat dong san", "Luật Kinh doanh BĐS"), ("luat xay dung", "Luật Xây dựng"),
 ("luat dia chat va khoang san", "Luật Địa chất & Khoáng sản"), ("luat khoang san", "Luật Địa chất & Khoáng sản"), ("luat quy hoach", "Luật Quy hoạch"), ("luat phong chay", "Luật PCCC"),
 ("luat thue", "Luật Thuế"), ("luat dau thau", "Luật Đấu thầu")]
def cluster(x):
    """Cụm = văn bản gốc (tên luật / số nghị định-thông tư) nếu nhận diện được, nếu không = chủ đề chính. Tin cùng cụm = cùng câu chuyện pháp lý."""
    t = strip(x["title"] + " " + x.get("summary", ""))
    hits = [(t.find(k), lab) for k, lab in LAWS if has(t, k)]
    hit = [i for i, (ks, _, _) in enumerate(REL) if i > 0 and any(has(t, k) for k in ks)]
    th = next((i for i in THEME_PREF.get(x["topics"][0], []) if i in hit), hit[0] if hit else None)  # chủ đề con: ưu tiên luật khớp đúng chủ đề chính
    x["theme"] = f"{x['topics'][0]}:{th}"
    if hits: lab = min(hits)[1]; return "law:" + re.sub(r"[^a-z0-9]+", "-", strip(lab)).strip("-"), lab
    m = re.search(r"(nghi dinh|thong tu|nghi quyet)\s*(?:so\s*)?(\d{1,4}/\d{4}(?:/[a-z\-]+)?)", t)
    if m: lab = {"nghi dinh": "Nghị định", "thong tu": "Thông tư", "nghi quyet": "Nghị quyết"}[m.group(1)] + " " + m.group(2).upper().replace("/ND-", "/NĐ-").replace("/QD-", "/QĐ-"); return "doc:" + re.sub(r"[^a-z0-9]+", "-", lab.lower()), lab
    if th is None: return "topic:" + x["topics"][0], TOPIC[x["topics"][0]][0]
    return f"theme:{x['topics'][0]}:{th}", THEME[th]
SUBJ = {"law:luat-dat-dai": "dat dai", "law:luat-nha-o": "nha o", "law:luat-kinh-doanh-bds": "kinh doanh bat dong san", "law:luat-xay-dung": "xay dung", "law:luat-pccc": "phong chay"}
def pick_home(items, n=6, floor=40, per_topic=2, min_n=5):
    """Trang chủ: tối đa 1 tin/cụm, tối đa 2 tin/chủ đề chính, điểm ≥ floor; thiếu thì bù tới min_n (vẫn 1 tin/cụm)."""
    out, cl, tp = [], set(), {}
    for relax in (False, True):
        for x in items:
            if len(out) >= (n if not relax else min_n): break
            if x["cluster"] in cl or x["theme"] in cl or x in out: continue  # khác văn bản VÀ khác chủ đề con (vd. giá đất)
            t = strip(x["title"])
            if sum(1 for c in cl if c in SUBJ and has(t, SUBJ[c])) >= 2: continue  # bài tổng hợp nhiều luật đã có trên trang chủ
            if not relax and (x["score"] < floor or tp.get(x["topics"][0], 0) >= per_topic): continue
            out.append(x); cl.update((x["cluster"], x["theme"])); tp[x["topics"][0]] = tp.get(x["topics"][0], 0) + 1
    return out
def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MasteriseSCMHub/1.0)"})
    return urllib.request.urlopen(r, timeout=20).read()
def parse(xml, srcname):
    out = []
    for it in ET.fromstring(xml).iter("item"):
        t = html.unescape((it.findtext("title") or "").strip()); u = (it.findtext("link") or "").strip()
        if not t or not u.startswith("http"): continue
        try: pub = parsedate_to_datetime(it.findtext("pubDate")).astimezone(TZ).isoformat(timespec="minutes")
        except Exception:
            try: pub = dt.datetime.strptime((it.findtext("pubDate") or "").strip(), "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=TZ).isoformat(timespec="minutes")  # chinhphu.vn format (giờ VN)
            except Exception: pub = None
        src = it.find("source"); name = src.text.strip() if src is not None and src.text else srcname
        if src is not None and " - " in t: t = t.rsplit(" - ", 1)[0].strip()
        summ = "" if src is not None else re.sub(r"<[^>]+>|\s+", " ", html.unescape(it.findtext("description") or "")).strip()[:300]
        st = strip(t + " " + summ)
        topics = [k for k, (_, ks) in TOPIC.items() if any(has(st, w) for w in ks)]
        if not topics or not any(has(st, w) for w in LEGAL): continue
        key = re.sub(r"[^a-z0-9]+", " ", strip(t)).strip()
        out.append(dict(id=hashlib.md5(key.encode()).hexdigest()[:12], title=unicodedata.normalize("NFC", t), url=u, source=name, summary=unicodedata.normalize("NFC", summ),
                        topics=topics, published=pub))
    return out
def main():
    try: old = json.load(open(OUT, encoding="utf-8"))
    except Exception: old = {}
    items = {x["id"]: x for x in old.get("items", [])}; errors = []; now = dt.datetime.now(TZ); used = {}
    srcs = [(GN.format(q=urllib.parse.quote(q)), "Google News", "Google News: " + q) for q in Q] + [(u, n, n) for n, u in RSS]
    for url, name, label in srcs:
        try:
            got = parse(get(url), name); used[label] = len(got)
            for x in got:
                if x["id"] in items: items[x["id"]].update(topics=x["topics"])
                else: items[x["id"]] = {**x, "found": now.isoformat(timespec="minutes")}
        except Exception as e: errors.append(f"{label}: {type(e).__name__}")
    cut = (now - dt.timedelta(days=KEEP_DAYS)).isoformat(); keep = []
    for x in items.values():
        if (x.get("published") or x.get("found") or "") < cut or (x.get("published") or "") > (now + dt.timedelta(hours=1)).isoformat(): continue
        x["score"], x["why"], x["parts"] = score(x, now); keep.append(x)
    keep.sort(key=lambda x: (-x["score"], -(dt.datetime.fromisoformat(x.get("published") or x["found"]).timestamp())))
    out, seen = [], []  # gộp tin trùng nội dung (cùng sự kiện, khác báo): Jaccard từ tiêu đề ≥ 0,5
    for x in keep:
        w = set(re.sub(r"[^a-z0-9]+", " ", strip(x["title"])).split())
        hit = next((o for o, ws in seen if len(w & ws) / max(1, len(w | ws)) >= 0.5), None)
        if hit is not None: hit.setdefault("also", []).append(dict(source=x["source"], url=x["url"])) if len(hit.get("also", [])) < 4 else None; continue
        x.pop("also", None); seen.append((x, w)); out.append(x)
    keep = out[:300]
    for x in keep: x["cluster"], x["cluster_label"] = cluster(x)
    size = {}
    for x in keep: size[x["cluster"]] = size.get(x["cluster"], 0) + 1
    home = [dict(id=x["id"], same=size[x["cluster"]] - 1) for x in pick_home(keep)]
    clusters = {c: dict(label=next(x["cluster_label"] for x in keep if x["cluster"] == c), n=k) for c, k in size.items()}
    labs = {}
    for c, v in clusters.items(): labs.setdefault(v["label"], []).append(c)
    for lab, cs in labs.items():  # tên cụm phải duy nhất: trùng thì thêm chủ đề chính
        if len(cs) > 1:
            for c in cs:
                tp = c.split(":")[1] if c.count(":") >= 1 and c.split(":")[1] in TOPIC else None
                th = int(c.split(":")[2]) if c.startswith("theme:") else None
                home_tp = next((k for k, v in THEME_PREF.items() if th in v), None)  # chủ đề "tự nhiên" của chủ đề con giữ tên gốc
                if tp and not c.startswith("law:") and tp != home_tp: clusters[c]["label"] = f"{lab} · {TOPIC[tp][0]}"
    assert len({v["label"] for v in clusters.values()}) == len(clusters), "duplicate cluster labels"
    for x in keep: x["cluster_label"] = clusters[x["cluster"]]["label"]
    json.dump(dict(schema_version=1, updated=now.isoformat(timespec="minutes"), window_days=KEEP_DAYS, topics={k: v[0] for k, v in TOPIC.items()},
                   note="Tin tự động từ RSS/Google News – CHƯA biên tập. Điểm & lý do sinh theo quy tắc từ khóa trong tiêu đề/tóm tắt; luôn đọc văn bản gốc.",
                   scoring="Điểm = Liên quan Masterise (≤60) + Tính mới/động lực văn bản (≤25: hiệu lực, ban hành, dự thảo, sửa đổi, loại văn bản) + Độ mới (≤20, giảm tuyến tính 30 ngày); tối đa 100.",
                   home=home, clusters=clusters, home_rule="Trang chủ: tối đa 1 tin/cụm văn bản và 1 tin/chủ đề con, 2 tin/chủ đề chính, điểm ≥ 40 (thiếu thì bù tới 5).",
                   sources=used, errors=errors, count=len(keep), items=keep), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"policy feed: {len(keep)} items, {len(errors)} errors")
if __name__ == "__main__": main()
