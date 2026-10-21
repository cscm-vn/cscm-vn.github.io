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
  const L = [["gia.html","Bảng giá","gia"],[fc || "#", "Dự báo" + (fc ? "" : " (sắp có)"),"dubao"],["xu-huong.html","Xu hướng","xuhuong"],["thi-truong.html","Thị trường","thitruong"],["scm.html","SCM","scm"],["nha-thau.html","Nhà thầu & CĐT","nhathau"],["thang.html","Tháng/năm","thang"],["huong-dan.html","Hướng dẫn","huongdan"]];
  host.innerHTML = `<div class="hn-bar"><div class="hn-in"><a class="skip" href="#main">Bỏ qua điều hướng</a><button class="hn-burger" aria-label="Mở menu" aria-expanded="false">☰</button>
   <a class="hn-logo" href="index.html" aria-label="Trang chủ – Masterise Procurement Hub"><i>M</i><span><b>Masterise</b><small>Procurement Hub</small></span></a>
   <nav class="hn-links" aria-label="Điều hướng chính"><button class="hn-mega-btn" aria-expanded="false" aria-haspopup="true">Danh mục ▾</button>${L.map(([h,l,k]) => `<a href="${h}" class="${k===page?"on":""}">${l}</a>`).join("")}</nav>
   <div class="hn-search"><input type="search" placeholder="Tìm vật tư, tin… (/)" aria-label="Tìm kiếm"><div class="hn-res"></div></div></div>
   <div class="mega"><div class="mega-in">${t ? t.tree.map(n => `<div><h4>${n.icon} ${HUB.catLink(n.id, n.name)}</h4><ul>${n.children.map(c => `<li>${HUB.catLink(c.id, c.name)}</li>`).join("")}</ul></div>`).join("") : ""}</div></div></div>`;
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
