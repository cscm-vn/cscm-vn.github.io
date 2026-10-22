/* Nhóm vật tư theo master data (data/mt.json ← data/registry/material_taxonomy.json).
   Dùng chung cho mọi trang có danh sách giá: MT.load(), MT.path(id, cat), MT.render(host, rows, opts). */
const MT = {};
MT.X = {code: "X", parent: null, level: 1, name_vi: "Chỉ số nguyên liệu & thị trường (ngoài master data)", virtual: true,
  description: "Không có trong master data của nhóm (kim loại, quặng, hạt nhựa thế giới, vàng, tỷ giá). Dùng để theo dõi chi phí đầu vào của các nhóm giá liên quan."};
MT.slug = s => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
MT.load = (base = "") => MT._p ||= fetch(base + "data/mt.json", {cache: "no-cache"}).then(r => r.ok ? r.json() : null).catch(() => null).then(d => {
  MT.css(); if (!d) return null; MT.d = d; MT.by = {X: MT.X}; d.nodes.forEach((n, i) => { n.ord = i; MT.by[n.code] = n; }); return d; });
MT.chain = code => { const p = []; while (code && MT.by[code]) { p.unshift(MT.by[code]); code = MT.by[code].parent; } return p; };
MT.virt = cat => { const c = "X." + (MT.slug(cat) || "khac"); return MT.by[c] ||= {code: c, parent: "X", level: 2, name_vi: cat || "Khác", virtual: true, ord: 9999}; };
MT.info = id => MT.d?.items?.[id] || null;
MT.path = (id, cat) => { const m = MT.info(id); return m && m.code ? MT.chain(m.code) : [MT.X, MT.virt(cat)]; };
MT.pathC = code => { const m = MT.d?.contract_items?.[code]; return m && m.code ? MT.chain(m.code) : [MT.X, MT.virt("Chưa ánh xạ")]; };
MT.text = (id, cat) => MT.path(id, cat).map(n => n.name_vi).join(" › ");
MT.conf = id => { const m = MT.info(id); return !m || !m.code ? "" : m.conf; };
MT.confPill = id => { const m = MT.info(id); if (!m) return ""; if (!m.code) return m.related_path?.length ? `<span class="mtg-cf" title="${MT.e(m.why)}. Ảnh hưởng tới: ${MT.e(m.related_path.join("; "))}">↗ ${MT.e(m.related_path.length)} nhóm giá liên quan</span>` : "";
  return m.conf === "high" ? "" : `<span class="mtg-cf ${m.conf}" title="${MT.e(m.why)}">${m.conf === "low" ? "gán tạm – cần xác nhận" : "gán theo vật tư đầu vào"}</span>`; };
MT.e = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
MT.med = a => { const s = a.slice().sort((x, y) => x - y), n = s.length; return n ? (n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2) : null; };
MT.fmt = v => (Math.abs(v) < 10 ? Math.abs(v).toFixed(1) : Math.abs(v).toFixed(0)).replace(".", ",");
/* Nhận định nhanh cho 1 nhóm: trung vị % thay đổi (ưu tiên 7 ngày → 30 ngày → lần cập nhật trước). */
MT.insight = (rows, na) => {
  const f0 = rows.filter(r => r.m?.s0 != null).map(r => r.m.f0).filter(Boolean).sort()[0];
  for (const [k, lb] of [["w1", "7 ngày"], ["mom", "30 ngày"], ["yoy", "1 năm"], ["s0", "đầu kỳ theo dõi" + (f0 ? " " + f0.slice(8, 10) + "/" + f0.slice(5, 7) : "")], ["d1", "lần cập nhật trước"]]) {
    const v = rows.map(r => r.m?.[k]).filter(x => x != null && isFinite(x)); if (!v.length) continue;
    if (k === "s0" && !v.some(x => Math.abs(x) > 0.05) && rows.some(r => r.m?.d1 != null && Math.abs(r.m.d1) > 0.05)) continue;
    const md = MT.med(v), up = v.filter(x => x > 0.05).length, dn = v.filter(x => x < -0.05).length, fl = v.length - up - dn;
    const cls = md > 0.3 ? "up" : md < -0.3 ? "dn" : "fl", word = cls === "up" ? "Tăng" : cls === "dn" ? "Giảm" : "Đi ngang";
    return `<span class="mtg-in ${cls}" title="Trung vị thay đổi giá của ${v.length} mã có dữ liệu so với ${lb}: ${up} mã tăng, ${dn} mã giảm, ${fl} mã đứng giá. ▲ đỏ = tăng (bất lợi bên mua), ▼ xanh = giảm.">${cls === "up" ? "▲" : cls === "dn" ? "▼" : "■"} ${word} ${cls === "fl" ? "" : MT.fmt(md) + "% "}<small>· ${lb} · ${up}↑ ${dn}↓ ${fl}=</small></span>`;
  }
  if (na) return `<span class="mtg-in na">${MT.e(na)}</span>`;
  return `<span class="mtg-in na" title="Mới có 1 điểm giá cho mỗi mã trong nhóm – chưa so sánh được">chưa đủ lịch sử (1 điểm giá)</span>`;
};
MT.css = () => { if (document.getElementById("mtg-css")) return; const s = document.createElement("style"); s.id = "mtg-css"; s.textContent = `
.mtg-bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0}.mtg-bar select{max-width:100%;min-width:0;flex:1 1 220px;padding:6px 8px;border:1px solid #d9dde3;border-radius:6px;font:inherit;font-size:13px;background:#fff}
.mtg-bar button{padding:6px 10px;border:1px solid #d9dde3;border-radius:6px;background:#fff;cursor:pointer;font:inherit;font-size:13px;color:inherit}.mtg-bar .mtg-lg{font-size:12px;color:#6b7785;flex-basis:100%}
.mtg-tw{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}.mtg-tw table{width:100%;border-collapse:collapse}
tr.mtg-h td{background:#f3efe6;border-bottom:1px solid #e3dccb;padding:7px 9px;white-space:normal;cursor:pointer}tr.mtg-h.lv1 td{background:#14325a;color:#fff;font-size:15px}tr.mtg-h.lv1 .mtg-n{background:#ffffff22;color:#fff}
tr.mtg-h.lv2 td{background:#efe7d6}tr.mtg-h.lv3 td{background:#f7f2e8}tr.mtg-h.lv4 td{background:#fbf8f2}
.mtg-hd{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;position:sticky;left:9px;max-width:min(100%,calc(100vw - 48px))}.mtg-t{font-weight:600}.mtg-c{display:inline-block;width:1.1em;transition:transform .15s}.mtg-h.cl .mtg-c{transform:rotate(-90deg)}
.mtg-n{font-size:11px;padding:1px 7px;border-radius:9px;background:#fff;color:#6b7785;border:1px solid #e3dccb}.mtg-s{font-size:11px;padding:1px 7px;border-radius:9px;background:#e8eef7;color:#14325a}
.mtg-in{font-size:12px;padding:2px 8px;border-radius:9px;background:#fff;border:1px solid #e3e6ea;color:#1d2733;font-weight:600}.mtg-in small{font-weight:400;color:#6b7785}.mtg-in.up{color:#b42318;border-color:#f3c3be}.mtg-in.dn{color:#067647;border-color:#b7e1cc}.mtg-in.na{font-weight:400;color:#6b7785}
tr.mtg-h.lv1 .mtg-in small{color:#6b7785}.mtg-ds{flex-basis:100%;font-size:11.5px;color:#6b7785;font-weight:400}tr.mtg-h.lv1 .mtg-ds{color:#d6deea}
.mtg-cf{display:inline-block;font-size:10.5px;padding:0 6px;border-radius:8px;background:#fff4e0;color:#9a6200;margin-left:4px;cursor:help}.mtg-cf.low{background:#fdecea;color:#b42318}
.mtg-pa{font-size:11px;color:#8a6d3b}.mtg-tw tbody tr:not(.mtg-h)>td:first-child,.mtg-tw thead th:first-child{min-width:160px}.mtg-hide{display:none!important}
@media(max-width:600px){tr.mtg-h td{font-size:13px}tr.mtg-h.lv1 td{font-size:14px}.mtg-ds{display:none}}`; document.head.appendChild(s); };
/* rows: [{path:[node...], html:'<tr>…</tr>', m:{w1,mom,d1}}]; opts: {head, cols, key, expand, note} */
MT.render = (host, rows, o = {}) => {
  MT.css(); const key = "mtg:" + (o.key || location.pathname), st = JSON.parse(localStorage.getItem(key) || "null");
  const tree = {code: "", kids: new Map(), rows: [], all: []};
  for (const r of rows) { let t = tree; t.all.push(r); for (const n of r.path) { if (!t.kids.has(n.code)) t.kids.set(n.code, {n, kids: new Map(), rows: [], all: []}); t = t.kids.get(n.code); t.all.push(r); } t.rows.push(r); }
  const ordKey = n => n.code === "X" ? 1e9 : ({KC: 0, MEPF: 1, HT: 2}[n.code] ?? n.ord ?? 0);
  const sorted = m => [...m.values()].sort((a, b) => ordKey(a.n) - ordKey(b.n) || a.n.name_vi.localeCompare(b.n.name_vi, "vi"));
  const opts = [], walk = (t, d) => { for (const k of sorted(t.kids)) { opts.push(`<option value="${MT.e(k.n.code)}">${"  ".repeat(d)}${d ? "└ " : ""}${MT.e(k.n.name_vi)} (${k.all.length})</option>`); walk(k, d + 1); } }; walk(tree, 0);
  const sel = host.querySelector(".mtg-f")?.value || o.group || "";
  let h = `<div class="mtg-bar"><select class="mtg-f" aria-label="Lọc theo nhóm master data"><option value="">Mọi nhóm master data (${rows.length} mã)</option>${opts.join("")}</select>
   <button type="button" class="mtg-ex">⊞ Mở tất cả</button><button type="button" class="mtg-co">⊟ Thu gọn tất cả</button>
   <span class="mtg-lg">Nhóm theo master data: Khối › Hệ › Nhóm giá › Nhóm giá cấp 2. Nhãn ở mỗi nhóm = trung vị % thay đổi giá của các mã trong nhóm (▲ đỏ tăng, ▼ xanh giảm). Bấm tiêu đề nhóm để mở/thu gọn.${o.note ? " " + o.note : ""}</span></div><div class="mtg-tw"><table class="${o.tcls || ""}">${o.head || ""}<tbody>`;
  const cols = o.cols || 8, emit = (t, anc) => { for (const k of sorted(t.kids)) { const n = k.n, a = anc.concat(n.code);
      h += `<tr class="mtg-h lv${n.level}" data-c="${MT.e(n.code)}" data-p="${MT.e(anc.join(" "))}" tabindex="0" aria-expanded="true"><td colspan="${cols}"><div class="mtg-hd"><span class="mtg-c" aria-hidden="true">▾</span><span class="mtg-t">${MT.e(n.name_vi)}</span><span class="mtg-n">${k.all.length} mã</span>${n.supply_now ? `<span class="mtg-s" title="Hiện trạng cấp vật tư theo ma trận quyết định">${MT.e(n.supply_now)}</span>` : ""}${MT.insight(k.all, o.naText)}${n.description && n.level >= 2 && !o.nodesc ? `<span class="mtg-ds">${MT.e(n.description)}</span>` : ""}</div></td></tr>`;
      for (const r of k.rows) h += r.html.replace(/^<tr/, `<tr data-p="${MT.e(a.join(" "))}"`); emit(k, a); } };
  emit(tree, []); h += `</tbody></table></div>`; if (!rows.length) h = `<div class="mtg-bar"></div><p class="mute">Không có mặt hàng phù hợp.</p>`;
  host.innerHTML = h; const f = host.querySelector(".mtg-f"); if (f) f.value = sel;
  const closed = new Set(o.expand ? [] : (st || o.defClosed || [])), trs = [...host.querySelectorAll("tbody > tr")];
  const apply = () => { const g = f?.value || ""; for (const tr of trs) { const p = (tr.dataset.p || "").split(" ").filter(Boolean), c = tr.dataset.c;
      const inG = !g || p.includes(g) || c === g || (c && MT.chain(g).some(n => n.code === c)); const hid = !inG || p.some(x => closed.has(x));
      tr.classList.toggle("mtg-hide", hid); if (c) { tr.classList.toggle("cl", closed.has(c)); tr.setAttribute("aria-expanded", !closed.has(c)); } }
    if (!o.expand) localStorage.setItem(key, JSON.stringify([...closed])); };
  host.querySelectorAll("tr.mtg-h").forEach(tr => { const t = () => { const c = tr.dataset.c; closed.has(c) ? closed.delete(c) : closed.add(c); apply(); };
    tr.onclick = e => { if (!e.target.closest("a,button,input,select")) t(); }; tr.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); t(); } }; });
  host.querySelector(".mtg-ex").onclick = () => { closed.clear(); apply(); };
  host.querySelector(".mtg-co").onclick = () => { trs.filter(t => t.dataset.c && !t.dataset.c.startsWith("X.") && (MT.by[t.dataset.c]?.level || 9) >= 2).forEach(t => closed.add(t.dataset.c)); trs.filter(t => t.dataset.c === "X").forEach(t => closed.add("X")); apply(); };
  if (f) f.onchange = () => { if (f.value) MT.chain(f.value).forEach(n => closed.delete(n.code)); o.onGroup?.(f.value); apply(); };
  apply();
};
/* Default for new visitors: Hệ/Nhóm giá headers visible, items under level ≥2 groups collapsed → short overview first. */
MT.defClosed = rows => [...new Set(rows.flatMap(r => r.path.filter(n => n.level >= 2).map(n => n.code)))];
window.MT = MT;
/* Thu gọn/mở cho bảng đã có hàng tiêu đề nhóm (vd tr.g ở trang Điều chỉnh giá): bấm tiêu đề → ẩn/hiện các dòng tới tiêu đề kế tiếp. */
MT.foldable = (tbl, sel = "tr.g") => { tbl.querySelectorAll(sel).forEach(g => { g.style.cursor = "pointer"; g.tabIndex = 0; g.setAttribute("aria-expanded", "true"); g.title = "Bấm để thu gọn / mở nhóm";
  const t = () => { const cl = g.getAttribute("aria-expanded") === "true"; g.setAttribute("aria-expanded", !cl); g.classList.toggle("cl", cl); let n = g.nextElementSibling; while (n && !n.matches(sel)) { n.classList.toggle("mtg-hide", cl); n = n.nextElementSibling; } };
  g.onclick = e => { if (!e.target.closest("a,button,input")) t(); }; g.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); t(); } }; }); };
