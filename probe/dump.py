import sys, re, json
from curl_cffi import requests as cr
from bs4 import BeautifulSoup
for slug in sys.argv[1:]:
    u = f"https://www.thitruonghanghoa.com/gia-ca-thi-truong-viet-nam/{slug}"
    h = cr.get(u, impersonate="chrome", timeout=30).text
    s = BeautifulSoup(h, "html.parser")
    lines = s.get_text("\n", strip=True).split("\n")
    print(f"DUMP {slug} nlines={len(lines)}")
    for i, l in enumerate(lines[:400]): print(f"DUMP {slug} {i:03d} {l[:140]}")
    # embedded JSON / script data hints
    for sc in s.find_all("script"):
        t = sc.string or ""
        if re.search(r"(xi m|PCB|gia|price)", t, re.I) and len(t) > 200:
            print(f"DUMPJS {slug} len={len(t)} {t[:600]!r}")
    print("DUMPAPI", sorted(set(re.findall(r"""["'](/api/[^"' ]+|https?://[^"' ]*api[^"' ]*)["']""", h)))[:30])
