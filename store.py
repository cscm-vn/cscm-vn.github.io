#!/usr/bin/env python3
"""Git-friendly canonical storage (see DATA.md).

Canonical (tracked in git, append-mostly text):
  data/registry/datasets.json        dataset registry + schema_version + column lists
  data/registry/items.json           item registry: one JSON object per line (meta + status)
  data/history/prices/YYYY-MM.csv    long-format price obs, 1 row per (item_id, date), latest fetch wins
  data/history/runs/YYYY-MM.csv      fetch run log (source, fetched_at, ok, n, error)
Derived (gitignored, rebuilt at any time):  data/prices.db  (SQLite working store for app/forecast)

CLI:  python store.py build [--db PATH]   # rebuild SQLite from CSV
      python store.py dump  [--db PATH]   # write CSV/JSON from SQLite
      python store.py check               # validate files (sorted, unique keys, schema)
"""
import csv, glob, io, json, os, sqlite3, sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DB = os.path.join(DATA, "prices.db")
REG = os.path.join(DATA, "registry")
HIST = os.path.join(DATA, "history")
SCHEMA_VERSION = 1

DATASETS = {
    "schema_version": SCHEMA_VERSION,
    "datasets": {
        "prices": {"path": "history/prices/{YYYY-MM}.csv", "partition": "month of date",
                   "key": ["item_id", "date"],
                   "columns": ["date", "item_id", "region", "source", "price", "price_high", "unit", "currency",
                               "change_pct", "fetched_at"],
                   "desc": "Giá quan sát (1 dòng/mặt hàng/ngày giá, lần lấy muộn nhất thắng)"},
        "runs": {"path": "history/runs/{YYYY-MM}.csv", "partition": "month of fetched_at",
                 "key": ["fetched_at", "source"], "columns": ["fetched_at", "source", "ok", "n", "error"],
                 "desc": "Nhật ký mỗi lần chạy nguồn"},
    },
    "registries": {"items": "registry/items.json"},
}
PCOLS = DATASETS["datasets"]["prices"]["columns"]
RCOLS = DATASETS["datasets"]["runs"]["columns"]

SQL = """
create table if not exists items(id text primary key, meta text, last_ok text, last_try text, status text);
create table if not exists obs(id text, fetched_at text, as_of text, price real, price_high real, change_pct real,
  primary key(id, fetched_at));
create table if not exists runs(source text, fetched_at text, ok int, n int, error text);
create index if not exists obs_id on obs(id, as_of);
"""

def _f(v):  # stable number formatting: shortest round-trip repr, ints without .0
    if v is None or v == "": return ""
    v = float(v)
    return str(int(v)) if v.is_integer() and abs(v) < 1e15 else repr(v)
def _n(s): return float(s) if s not in ("", None) else None

def _write(path, text):
    """Write only if content changed (keeps mtimes/git clean)."""
    if os.path.exists(path) and open(path, encoding="utf-8").read() == text: return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"; open(tmp, "w", encoding="utf-8", newline="").write(text); os.replace(tmp, path); return True

def _csv(cols, rows):
    b = io.StringIO(); w = csv.writer(b, lineterminator="\n"); w.writerow(cols); w.writerows(rows); return b.getvalue()

def has_text():
    return os.path.exists(os.path.join(REG, "items.json"))

# ---------------- SQLite -> text ----------------
def dump(con):
    con.row_factory = None
    items = {i: (json.loads(m), lo, lt, st) for i, m, lo, lt, st in con.execute("select id, meta, last_ok, last_try, status from items")}
    lines = []
    for i in sorted(items):
        m, lo, lt, st = items[i]
        lines.append(json.dumps({"id": i, "status": st, "last_ok": lo, "last_try": lt,
                                 "meta": {k: v for k, v in m.items() if k != "backfill"}}, ensure_ascii=False, sort_keys=True))
    _write(os.path.join(REG, "items.json"), "[\n" + ",\n".join(lines) + "\n]\n")
    _write(os.path.join(REG, "datasets.json"), json.dumps(DATASETS, ensure_ascii=False, indent=1) + "\n")
    # prices: one row per (id, as_of) – the latest fetched_at wins
    q = """select id, as_of, fetched_at, price, price_high, change_pct from (
             select o.*, row_number() over (partition by id, coalesce(as_of, substr(fetched_at,1,10))
                                            order by fetched_at desc) rn from obs o) where rn=1"""
    months = {}
    for i, a, f, p, ph, cp in con.execute(q):
        d = a or f[:10]; m = items.get(i, ({},))[0]
        months.setdefault(d[:7], []).append([d, i, m.get("region") or "", (m.get("src") or "").split(" [")[0],
                                             _f(p), _f(ph), m.get("unit") or "", m.get("currency") or "", _f(cp), f])
    for mo, rows in months.items():
        rows.sort(key=lambda r: (r[0], r[1]))
        _write(os.path.join(HIST, "prices", mo + ".csv"), _csv(PCOLS, rows))
    rm = {}
    for s, f, ok, n, e in con.execute("select source, fetched_at, ok, n, error from runs order by rowid"):
        rm.setdefault(f[:7], []).append([f, s, ok, n, (e or "").replace("\n", " ")])
    for mo, rows in rm.items():
        rows.sort(key=lambda r: r[0])  # stable: keeps source order within a run
        _write(os.path.join(HIST, "runs", mo + ".csv"), _csv(RCOLS, rows))

# ---------------- text -> SQLite ----------------
def iter_prices():
    for p in sorted(glob.glob(os.path.join(HIST, "prices", "*.csv"))):
        with open(p, encoding="utf-8", newline="") as fh: yield from csv.DictReader(fh)

def build(db=DB):
    """(Re)build the SQLite working store from the canonical text files. Returns open connection."""
    if not has_text():
        if os.path.exists(db):   # one-time migration of a legacy db
            c = sqlite3.connect(db); c.executescript(SQL); dump(c); c.close()
        else:
            c = sqlite3.connect(db); c.executescript(SQL); return c
    tmp = db + ".building"
    if os.path.exists(tmp): os.remove(tmp)
    c = sqlite3.connect(tmp); c.executescript(SQL)
    for r in json.load(open(os.path.join(REG, "items.json"), encoding="utf-8")):
        c.execute("insert into items values(?,?,?,?,?)", (r["id"], json.dumps(r["meta"], ensure_ascii=False),
                                                         r["last_ok"], r["last_try"], r["status"]))
    c.executemany("insert or replace into obs values(?,?,?,?,?,?)",
                  ((r["item_id"], r["fetched_at"], r["date"], _n(r["price"]), _n(r["price_high"]), _n(r["change_pct"]))
                   for r in iter_prices()))
    for p in sorted(glob.glob(os.path.join(HIST, "runs", "*.csv"))):
        with open(p, encoding="utf-8", newline="") as fh:
            c.executemany("insert into runs values(?,?,?,?,?)",
                          ((r["source"], r["fetched_at"], int(r["ok"]), int(r["n"]), r["error"] or None) for r in csv.DictReader(fh)))
    c.commit(); c.close(); os.replace(tmp, db)
    return sqlite3.connect(db)

def ensure_db(db=DB):
    """For readers (app.py, forecast): rebuild db if missing or older than the text files."""
    srcs = glob.glob(os.path.join(HIST, "*", "*.csv")) + [os.path.join(REG, "items.json")]
    newest = max((os.path.getmtime(p) for p in srcs if os.path.exists(p)), default=0)
    if has_text() and (not os.path.exists(db) or os.path.getmtime(db) < newest): build(db).close()
    return db

def check():
    seen, errs, n = set(), [], 0
    for p in sorted(glob.glob(os.path.join(HIST, "prices", "*.csv"))):
        rows = list(csv.reader(open(p, encoding="utf-8", newline="")))
        if rows[0] != PCOLS: errs.append(f"{p}: bad header")
        body = rows[1:]; n += len(body)
        if body != sorted(body, key=lambda r: (r[0], r[1])): errs.append(f"{p}: not sorted")
        for r in body:
            if not r[0].startswith(os.path.basename(p)[:7]): errs.append(f"{p}: {r[0]} wrong partition")
            if (r[1], r[0]) in seen: errs.append(f"dup {r[1]} {r[0]}")
            seen.add((r[1], r[0])); float(r[4])
    print(f"prices rows={n} errors={len(errs)}"); [print(" ", e) for e in errs[:20]]
    return not errs

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    db = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else DB
    if cmd == "build": build(db).close(); print("built", db)
    elif cmd == "dump": c = sqlite3.connect(db); dump(c); c.close(); print("dumped from", db)
    else: sys.exit(0 if check() else 1)
