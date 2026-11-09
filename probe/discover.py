#!/usr/bin/env python3
"""Download selected appendices (Drive file IDs) of Sở XD TP.HCM price notices into probe/files/."""
import os
from curl_cffi import requests as cr
OUT = "probe/files"; os.makedirs(OUT, exist_ok=True)
F = {"t9_pl02": "1GmWZdNMap_bVSezxR0w_HD7Lgcr4NEMT", "t9_pl07": "1wJXgm6hsoBGLuofZgZr4moOlFlbUUEnY",
     "t9_pl09": "1XbA8usdGUs5ysq-_SHSmQ8yrH2Cws9BJ", "t9_pl10": "1g71vGbVC-dMEQ6ktADxFtOcb4OdM1_Xt",
     "t8_pl02": "14cFo-mDdnA9Y1NBNXs5SuTqu0ts3x8yi", "t8_pl07": "1iiSrcl3f8SzAdlT07XJCq79uvFNi1Nb6",
     "t8_pl09": "10fNmXlUQppgN-h_GIG20cAyPswPjVPqa", "t8_pl10": "1Uj11PZIsB8Ub9bfHNDCWi9c6sKVa-ff3"}
for k, did in F.items():
    r = cr.get(f"https://drive.usercontent.google.com/download?id={did}&export=download&confirm=t", impersonate="chrome", timeout=120)
    ok = r.content[:4] == b"%PDF"
    print("DL", k, r.status_code, len(r.content) // 1024, "kB", "PDF" if ok else repr(r.content[:80]))
    if ok: open(os.path.join(OUT, k + ".pdf"), "wb").write(r.content)
