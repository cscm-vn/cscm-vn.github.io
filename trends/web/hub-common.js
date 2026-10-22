/* Shared nav, data loading & helpers for every hub page (Vietnamese UI). */
const HUB = {cache:{}};
HUB.get = async (f) => HUB.cache[f] ||= fetch("data/" + f, {cache: "no-cache"}).then(r => r.ok ? r.json() : null).catch(() => null);
HUB.esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
HUB.strip = s => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
HUB.num = (v, d) => v == null ? "–" : Number(v).toLocaleString("vi-VN", {maximumFractionDigits: d ?? (Math.abs(v) < 100 ? 2 : 0)});
HUB.pct = v => v == null ? '<span class="mute">–</span>' : `<span class="${v > 0 ? "up" : v < 0 ? "down" : ""}">${v > 0 ? "▲" : v < 0 ? "▼" : ""}${Math.abs(v).toFixed(Math.abs(v) < 10 ? 2 : 1).replace(".", ",")}%</span>`;
HUB.date = s => s ? s.slice(0, 10).split("-").reverse().join("/") : "";
HUB.qs = k => new URLSearchParams(location.search).get(k);
HUB.regPill = r => r === "hn" ? '<span class="pill hn">Hà Nội / Bắc</span>' : r === "hcm" ? '<span class="pill hcm">TP.HCM / Nam</span>' : r === "world" ? '<span class="pill">Thế giới</span>' : "";
HUB.tax = async () => {
  const t = await HUB.get("taxonomy.json"); if (!t) return null;
  if (!t.byId) { t.byId = {}; for (const n of t.tree) { t.byId[n.id] = {...n, level: 1}; for (const c of n.children) t.byId[c.id] = {...c, level: 2, parent: n}; } }
  return t;
};
HUB.catLink = (id, label) => `<a href="danh-muc.html?c=${encodeURIComponent(id)}">${HUB.esc(label)}</a>`;
HUB.crumb = async (parts) => { const el = document.getElementById("crumb"); if (el) el.innerHTML = [`<a href="index.html">Trang chủ</a>`, ...parts].join(" › "); };
HUB.nav = async () => {
  if (!document.querySelector("link[rel=icon]")) { const l = document.createElement("link"); l.rel = "icon"; l.type = "image/svg+xml"; l.href = "favicon.svg"; document.head.appendChild(l); }
  const host = document.getElementById("hubnav"); if (!host) return;
  const page = document.body.dataset.page || ""; const t = await HUB.tax(); const cfg = await HUB.get("site-config.json") || {};
  const fc = cfg.forecast_page;
  const L = [["gia.html","Bảng giá","gia"],["dieu-chinh.html","Điều chỉnh giá HĐ","dieuchinh","hot"],[fc || "#", "Dự báo" + (fc ? "" : " (sắp có)"),"dubao"],["xu-huong.html","Xu hướng","xuhuong"],["thi-truong.html","Thị trường","thitruong"],["scm.html","SCM","scm"],["nha-thau.html","Nhà thầu & CĐT","nhathau"],["thang.html","Tháng/năm","thang"],["huong-dan.html","Hướng dẫn","huongdan"]];
  host.innerHTML = `<div class="hn-bar"><div class="hn-in"><a class="skip" href="#main">Bỏ qua điều hướng</a><button class="hn-burger" aria-label="Mở menu" aria-expanded="false">☰</button>
   <a class="hn-logo" href="index.html" aria-label="Trang chủ – Masterise Construction SCM Hub"><span class="hn-mark" aria-hidden="true"><img src="masterise-logo.svg" alt="" width="27" height="38" decoding="async"><span class="hn-glint"></span></span><span class="hn-word"><b>Masterise</b><small><span class="hn-long">Construction </span>SCM Hub</small></span></a>
   <nav class="hn-links" aria-label="Điều hướng chính"><button class="hn-mega-btn" aria-expanded="false" aria-haspopup="true">Danh mục ▾</button>${L.map(([h,l,k,x]) => `<a href="${h}" class="${[k===page?"on":"",x||""].join(" ").trim()}"${x ? ' title="Theo dõi giá thị trường so với đơn giá HĐ tổng thầu (CTD/NTC) – vượt ngưỡng điều chỉnh"' : ""}>${x ? "⚖️ " : ""}${l}${x ? '<span class="hn-badge" hidden></span>' : ""}</a>`).join("")}</nav>
   <div class="hn-search"><input type="search" placeholder="Tìm vật tư, tin… (/)" aria-label="Tìm kiếm"><div class="hn-res"></div></div></div>
   <div class="mega"><div class="mega-in">${t ? t.tree.map(n => `<div><h4>${n.icon} ${HUB.catLink(n.id, n.name)}</h4><ul>${n.children.map(c => `<li>${HUB.catLink(c.id, c.name)}</li>`).join("")}</ul></div>`).join("") : ""}</div></div></div>`;
  HUB.get("dieu-chinh-summary.json").then(d => { const S = d?.contracts?.[0]?.summary?.all, b = host.querySelector(".hn-badge"); if (!S || !b) return;
    const n = Math.max(S.ctd.down, S.ntc.down); if (!n) return; b.textContent = n; b.title = `${S.ctd.down} mục vượt ngưỡng GIẢM vs CTD, ${S.ntc.down} vs NTC (2 miền)`; b.hidden = false; });
  const mega = host.querySelector(".mega"), links = host.querySelector(".hn-links");
  host.querySelector(".hn-mega-btn").onclick = e => { e.stopPropagation(); e.currentTarget.setAttribute("aria-expanded", mega.classList.toggle("open")); };
  host.querySelector(".hn-burger").onclick = e => { e.stopPropagation(); e.currentTarget.setAttribute("aria-expanded", links.classList.toggle("open")); };
  document.addEventListener("click", e => { if (!host.contains(e.target)) { mega.classList.remove("open"); links.classList.remove("open"); res.style.display = "none"; } });
  const inp = host.querySelector("input"), res = host.querySelector(".hn-res");
  document.addEventListener("keydown", e => { if (e.key === "/" && document.activeElement.tagName !== "INPUT") { e.preventDefault(); inp.focus(); } if (e.key === "Escape") { res.style.display = "none"; mega.classList.remove("open"); } });
  let idx = null;
  inp.oninput = async () => {
    const q = HUB.strip(inp.value.trim()); if (q.length < 2) { res.style.display = "none"; return; }
    if (!idx) { const [h, tr, mk] = await Promise.all([HUB.get("hub.json"), HUB.get("trends.json"), HUB.get("market.json")]); idx = [];
      idx.push({k: "Trang", t: "Điều chỉnh giá HĐ tổng thầu – giá thị trường vs đơn giá CTD/NTC, vượt ngưỡng", u: "dieu-chinh.html"});
      if (t) for (const id in t.byId) idx.push({k: "Danh mục", t: t.byId[id].name, u: `danh-muc.html?c=${id}`});
      for (const x of h?.items || []) idx.push({k: "Giá", t: `${x.name}${x.region ? " – " + x.region : ""}`, u: `mat-hang.html?id=${encodeURIComponent(x.id)}`});
      for (const x of tr?.items || []) idx.push({k: "Xu hướng", t: x.title, u: `xu-huong.html?id=${x.id}`});
      for (const x of mk?.items || []) idx.push(x.org_type ? {k: x.org_type === "contractor" ? "Nhà thầu" : "Chủ đầu tư", t: x.title, u: `nha-thau.html?t=${x.org_type}&org=${encodeURIComponent(x.org)}`} : {k: "Thị trường", t: x.title, u: `thi-truong.html?id=${x.id}`});
      const scm = await HUB.get("scm.json"); for (const c of scm?.categories || []) idx.push({k: "SCM", t: `${c.name} – cung cầu & sourcing`, u: `scm.html?c=${c.id}`});
      idx.forEach(x => x.s = HUB.strip(x.t)); }
    const words = q.split(/\s+/); const hits = idx.filter(x => words.every(w => x.s.includes(w))).slice(0, 25);
    res.innerHTML = hits.length ? hits.map(x => `<a href="${x.u}"><span class="k">${x.k}</span>${HUB.esc(x.t)}</a>`).join("") : '<div style="padding:10px" class="mute">Không tìm thấy</div>';
    res.style.display = "block";
  };
  inp.onkeydown = e => { if (e.key === "Enter") { const a = res.querySelector("a"); if (a) location.href = a.href; } };
  HUB.views();
};
// Lượt xem (GoatCounter public counter API + views-daily.json do workflow tạo). Lỗi => ẩn, không ném lỗi.
HUB.views = async () => {
  if (document.querySelector(".hn-views")) return;
  const GC = "https://cscm-vn.goatcounter.com/counter/", nf = new Intl.NumberFormat("vi-VN"), SINCE = "2026-10-22";
  const get = async (u, raw) => { try { const c = new AbortController(); const t = setTimeout(() => c.abort(), 6000);
    const r = await fetch(raw ? u : GC + u, {signal: c.signal, credentials: "omit"}); clearTimeout(t); if (!r.ok) return null;
    const j = await r.json(); return raw ? j : (+String(j.count).replace(/\D/g, "") || 0); } catch (e) { return null; } };
  const ymd = d => new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Ho_Chi_Minh"}).format(d);  // ngày giờ VN
  const day = ymd(new Date()), next = ymd(new Date(Date.now() + 864e5));
  const home = /(^|\/)(index\.html)?$/.test(location.pathname);
  const [tot, today, p1, p2] = await Promise.all([get(`TOTAL.json?start=${SINCE}&end=${next}`), get(`TOTAL.json?start=${day}&end=${next}`),
    home ? get("%2F.json") : null, home ? get("%2Findex.html.json") : null]);
  if (tot == null) return;
  const wrap = document.createElement("div"); wrap.className = "hn-views-wrap";
  const it = (l, v, tip) => v == null ? "" : `<span title="${tip || ""}"><small>${l}</small><b>${nf.format(v)}</b></span>`;
  wrap.innerHTML = `<button type="button" class="hn-views" aria-expanded="false" aria-controls="hn-vchart" title="Xem xu hướng 30 ngày">
    <i aria-hidden="true">◉</i>${it("Lượt xem hôm nay", today, "Theo ngày giờ Việt Nam")}${it("Tổng lượt xem", tot, "Toàn trang, từ 22/10/2026")}${home && (p1 != null || p2 != null) ? it("Trang chủ", (p1 || 0) + (p2 || 0)) : ""}<em aria-hidden="true">▾</em></button>
    <div class="hn-vchart" id="hn-vchart" hidden></div>`;
  document.body.appendChild(wrap);
  const btn = wrap.querySelector("button"), box = wrap.querySelector(".hn-vchart"); let loaded = false;
  btn.onclick = async () => {
    const open = box.hidden; box.hidden = !open; btn.setAttribute("aria-expanded", open);
    if (!open || loaded) return; loaded = true; box.innerHTML = '<div class="vc-empty">Đang tải…</div>';
    const d = await get("views-daily.json?t=" + Math.floor(Date.now() / 6e5), true);
    if (!d || !Array.isArray(d.days) || !d.days.length) { box.innerHTML = '<div class="vc-empty">Chưa có dữ liệu xu hướng.</div>'; return; }
    const D = d.days, max = Math.max(1, ...D.map(x => x.n || 0)), W = 600, H = 120, bw = W / D.length;
    const lab = s => { const [y, m, dd] = s.split("-"); return `${dd}/${m}`; };
    const bars = D.map((x, k) => { const h = x.n ? Math.max(2, x.n / max * (H - 8)) : 0;
      return `<g class="vb" data-k="${k}"><rect x="${k * bw}" y="0" width="${bw}" height="${H}" fill="transparent"/>` +
        (x.n == null ? `<rect x="${k * bw + bw * .2}" y="${H - 2}" width="${bw * .6}" height="2" class="na"/>` : `<rect x="${k * bw + bw * .15}" y="${H - h}" width="${bw * .7}" height="${h}" rx="2"/>`) +
        `<title>${lab(x.d)}: ${x.n == null ? "chưa đo" : nf.format(x.n) + " lượt xem"}</title></g>`; }).join("");
    const sum = D.reduce((s, x) => s + (x.n || 0), 0);
    box.innerHTML = `<div class="vc-h"><b>Lượt xem theo ngày</b><span>30 ngày gần nhất · ${nf.format(sum)} lượt</span></div>
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Biểu đồ lượt xem 30 ngày">${bars}</svg>
      <div class="vc-x"><span>${lab(D[0].d)}</span><span class="vc-tip" aria-live="polite">Rê chuột/chạm vào cột để xem số</span><span>${lab(D[D.length - 1].d)}</span></div>
      <div class="vc-f">Theo giờ Việt Nam · cập nhật ${String(d.updated || "").slice(11, 16)} ${String(d.updated || "").slice(8, 10)}/${String(d.updated || "").slice(5, 7)}</div>`;
    const tip = box.querySelector(".vc-tip");
    box.querySelectorAll(".vb").forEach(g => { const x = D[+g.dataset.k];
      const show = () => { box.querySelectorAll(".vb.on").forEach(e => e.classList.remove("on")); g.classList.add("on");
        tip.textContent = `${lab(x.d)}/${x.d.slice(0, 4)}: ${x.n == null ? "chưa đo" : nf.format(x.n) + " lượt xem"}`; };
      g.addEventListener("mouseenter", show); g.addEventListener("click", show); });
  };
};
HUB.sidebar = async (el, active, counts) => {
  if (!el) return; const t = await HUB.tax(); if (!t) return; const act = t.byId[active]; const open = act ? (act.level === 1 ? act.id : act.parent.id) : null;
  el.innerHTML = `<button class="chip side-toggle" onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden">☰ Cây danh mục</button><div>` + t.tree.map(n => {
    const c = n.children.reduce((s, x) => s + (counts?.[x.id] || 0), 0);
    return `<details ${n.id === open ? "open" : ""}><summary class="${n.id === active ? "on" : ""}">${n.icon} ${HUB.esc(n.name)}</summary>
    <a href="danh-muc.html?c=${n.id}" class="${n.id === active ? "on" : ""}"><i>Tổng quan nhóm</i><span class="cnt">${c || ""}</span></a>` +
    n.children.map(x => `<a href="danh-muc.html?c=${x.id}" class="${x.id === active ? "on" : ""}">${HUB.esc(x.name)}<span class="cnt">${counts?.[x.id] || ""}</span></a>`).join("") + "</details>";
  }).join("") + "</div>";
  if (innerWidth < 900) { const d = el.querySelector(".side-toggle + div"); d.hidden = true; }
};
HUB.foot = (extra) => { const f = document.getElementById("foot"); if (f) f.innerHTML = `${extra || ""} Giá tham khảo từ nguồn công khai, chưa VAT/vận chuyển trừ khi ghi chú; không thay thế báo giá chính thức. Xu hướng do nhóm mua sắm & trợ lý nghiên cứu, mỗi mục có nguồn để kiểm chứng.`; };
document.addEventListener("DOMContentLoaded", HUB.nav);
