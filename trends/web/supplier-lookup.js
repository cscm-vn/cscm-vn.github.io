/* Bảng "Tra cứu nhà cung cấp" (nha-thau.html). Dữ liệu dựng sẵn: data/suppliers.json (trends/supplier_profiles.py). Không gọi API ngoài từ trình duyệt. */
(async () => {
 const root = document.getElementById("ncc"); if (!root) return;
 const E = HUB.esc, out = document.getElementById("ncc-out"), inp = document.getElementById("ncc-q"), list = document.getElementById("ncc-list");
 const [D, fd, mk] = await Promise.all([HUB.get("suppliers.json"), HUB.get("feed.json"), HUB.get("market.json")]);
 if (!D || !D.units) { out.innerHTML = '<div class="ncc-empty">Không tải được dữ liệu tra cứu. Vui lòng tải lại trang.</div>'; return; }
 const U = D.units, BY = Object.fromEntries(U.map(u => [u.id, u])); U.forEach(u => u.s = HUB.strip([u.name, u.short, u.org, u.mst, u.ticker || "", ...u.aliases].join(" ")));
 const NOW = new Date(), dayDiff = s => Math.floor((NOW - new Date(s + "T00:00:00")) / 864e5), dmy = s => s ? s.split("-").reverse().join("/") : "";
 const T = v => v == null ? "–" : (v / 1e9).toLocaleString("vi-VN", {maximumFractionDigits: Math.abs(v / 1e9) >= 100 ? 0 : 1}),
  X = (v, d = 2) => v == null ? "–" : v.toLocaleString("vi-VN", {maximumFractionDigits: d, minimumFractionDigits: d}),
  PC = v => v == null ? "–" : (v * 100).toLocaleString("vi-VN", {maximumFractionDigits: 1, minimumFractionDigits: 1}) + "%";
 const SEV = {bad: "⛔", warn: "⚠️", info: "ℹ️"}, LAB = {good: "✓ Tốt", watch: "◔ Theo dõi", caution: "⚠ Thận trọng", nodata: "? Chưa đủ dữ liệu"};
 const NOISE = /(nguoi (dang|tung)|thong tin sai|bia chuyen|tin don|cau view|dang tin)/; // bài nói về người tung tin đồn, không phải rủi ro của đơn vị
 const RISK = /(no thue|truy thu|cuong che|xu phat|vi pham|khoi to|bi bat|bi kien|bi khoi kien|vu kien|tranh chap|pha san|giai the|thua lo|lo rong|cham tra|no xau|dinh chi|thanh tra|lua dao)/;
 let cmp = [], cur = null, act = -1, shown = [];
 const find = q => {
  const s = HUB.strip(q).trim(); if (!s) return []; const digits = s.replace(/\s/g, ""), isMst = /^\d{3,}$/.test(digits), w = s.split(/\s+/);
  const r = [];
  for (const u of U) {
   let k = 9;
   if (isMst) { if (u.mst === digits) k = 0; else if (u.mst.startsWith(digits)) k = 1; else if (u.mst.includes(digits)) k = 2; }
   else if (w.every(x => u.s.includes(x))) { const al = u.aliases; k = al.includes(s) ? 0 : al.some(a => a.startsWith(s)) ? 1 : HUB.strip(u.name).includes(s) ? 2 : 3; }
   if (k < 9) r.push([k, u]);
  }
  return r.sort((a, b) => a[0] - b[0] || (b[1].listed - a[1].listed) || a[1].org.localeCompare(b[1].org, "vi")).map(x => x[1]);
 };
 const opt = (u, i) => `<li role="option" id="ncc-o${i}" data-id="${u.id}" aria-selected="${i === act}"><b>${E(u.short)}</b> <span class="small mute">· ${E(u.mst)}${u.ticker ? " · " + E(u.ticker) + " (" + E(u.exchange) + ")" : ""}</span><span class="small">${E(u.name)}</span></li>`;
 const closeList = () => { list.hidden = true; inp.setAttribute("aria-expanded", "false"); inp.removeAttribute("aria-activedescendant"); act = -1; };
 const links = () => D.links.map(l => `<li><a href="${E(l.u)}" target="_blank" rel="noopener">${E(l.t)} ↗</a> <span class="small mute">– ${E(l.why)}</span></li>`).join("");
 const notFound = q => {
  const dg = q.replace(/\s/g, ""), isNum = /^\d+$/.test(dg);
  out.innerHTML = `<div class="ncc-empty"><h3>“${E(q.trim())}” chưa có trong dữ liệu</h3>
   <p style="margin:0 0 6px">Bảng này chỉ chứa ${U.length} nhà thầu / nhà cung cấp hub đang theo dõi và <b>không</b> tra trực tiếp trên mạng. ${isNum && ![10, 13].includes(dg.length) ? "Lưu ý: mã số thuế thường có 10 hoặc 13 chữ số – kiểm tra lại số vừa nhập. " : ""}Bạn có thể tra ngay ở nguồn chính thức:</p>
   <ul class="ncc-todo">${links()}</ul></div>`;
 };
 const pick = id => { const u = BY[id]; if (!u) return; cur = u; cmp = cmp.filter(x => x !== id); inp.value = u.short; closeList(); render(); };
 const onInput = () => {
  const q = inp.value; if (!q.trim()) { closeList(); return; }
  shown = find(q).slice(0, 8); act = shown.length ? 0 : -1;
  list.innerHTML = shown.length ? shown.map(opt).join("") : '<li class="ncc-none" role="option" aria-disabled="true">Không có gợi ý – nhấn Enter để xem hướng dẫn tra nguồn chính thức</li>';
  list.hidden = false; inp.setAttribute("aria-expanded", "true"); if (shown.length) inp.setAttribute("aria-activedescendant", "ncc-o0");
 };
 inp.addEventListener("input", onInput); inp.addEventListener("focus", () => { if (inp.value.trim() && !cur) onInput(); });
 inp.addEventListener("keydown", e => {
  if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); if (list.hidden) onInput(); if (!shown.length) return; act = (act + (e.key === "ArrowDown" ? 1 : -1) + shown.length) % shown.length;
   list.querySelectorAll("li").forEach((li, i) => li.setAttribute("aria-selected", i === act)); inp.setAttribute("aria-activedescendant", "ncc-o" + act); list.children[act].scrollIntoView({block: "nearest"}); }
  else if (e.key === "Enter") { e.preventDefault(); const q = inp.value; if (!q.trim()) return; const r = shown.length && !list.hidden ? shown : find(q); if (r.length) pick((r[Math.max(act, 0)] || r[0]).id); else { cur = null; closeList(); notFound(q); } }
  else if (e.key === "Escape") closeList();
 });
 list.addEventListener("mousedown", e => { const li = e.target.closest("li[data-id]"); if (li) { e.preventDefault(); pick(li.dataset.id); } });
 document.addEventListener("click", e => { if (!root.contains(e.target)) closeList(); });
 document.getElementById("ncc-quick").addEventListener("click", e => { const b = e.target.closest("button[data-id]"); if (b) pick(b.dataset.id); });
 // ---- render ----
 const trendSvg = (vals, nm) => { // vals: cũ -> mới
  const w = 64, h = 24, n = vals.length, mx = Math.max(...vals.map(Math.abs), 1), hasNeg = vals.some(x => x < 0), base = hasNeg ? h / 2 : h - 1, bw = Math.floor((w - (n - 1) * 3) / n);
  const bars = vals.map((v, i) => { const hh = Math.max(1.5, Math.abs(v) / mx * (hasNeg ? h / 2 - 1 : h - 3)), y = v < 0 ? base : base - hh; return `<rect class="${i === n - 1 ? "l" : v < 0 ? "n" : "p"}" x="${i * (bw + 3)}" y="${y.toFixed(1)}" width="${bw}" height="${hh.toFixed(1)}" rx="1.5"/>`; }).join("");
  return `<svg class="ncc-trend" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="Xu hướng ${E(nm)}: ${vals.map(v => T(v) + " tỷ").join(" → ")}">${bars}</svg>`;
 };
 const ROWS = [
  ["Doanh thu thuần", p => p.v.rev, "t", 1], ["Lợi nhuận gộp", p => p.v.gp, "t"], ["– Biên lợi nhuận gộp", p => p.m.gm, "p"], ["Lợi nhuận trước thuế", p => p.v.pbt, "t"],
  ["Lợi nhuận sau thuế (LNST)", p => p.v.np, "t", 1], ["– Biên lợi nhuận ròng", p => p.m.nm, "p"], ["Tổng tài sản", p => p.v.ta, "t"], ["Nợ phải trả", p => p.v.liab, "t"],
  ["Vốn chủ sở hữu", p => p.v.eq, "t"], ["Nợ phải trả ÷ vốn chủ", p => p.m.de, "x"], ["Nợ vay (ngắn + dài hạn)", p => p.m.debt, "t"], ["Nợ vay ÷ vốn chủ", p => p.m.dbe, "x"],
  ["Thanh khoản hiện hành (TSNH ÷ nợ NH)", p => p.m.cr, "x"], ["Phải thu khách hàng", p => p.v.ar, "t"], ["Số ngày thu tiền", p => p.m.dso, "d"], ["Hàng tồn kho", p => p.v.inv, "t"],
  ["Tiền + đầu tư tài chính ngắn hạn", p => p.v.cash + p.v.sti, "t"], ["Dòng tiền kinh doanh (CFO)", p => p.v.cfo, "t", 1]];
 const fmt = (v, k) => k === "t" ? T(v) : k === "p" ? PC(v) : k === "x" ? X(v) : X(v, 0);
 const delta = (a, b, k) => { if (a == null || b == null) return "–";
  if (k === "t") { if (b <= 0 || a <= 0) return (a >= 0) === (b >= 0) ? "–" : "đổi dấu"; const d = a / b - 1; return `<span class="${d >= 0 ? "up" : "down"}" style="color:var(--mute)">${d >= 0 ? "▲" : "▼"} ${(Math.abs(d) * 100).toLocaleString("vi-VN", {maximumFractionDigits: 1})}%</span>`; }
  const d = k === "p" ? (a - b) * 100 : a - b; return `${d >= 0 ? "+" : "−"}${Math.abs(d).toLocaleString("vi-VN", {maximumFractionDigits: k === "d" ? 0 : 1})}${k === "p" ? " đ.%" : k === "d" ? " ngày" : ""}`; };
 const periodDesc = f => f.periods[0].label;
 const finTable = f => {
  const P = f.periods, rev = [...P].reverse();
  const head = `<tr><th class="l">Chỉ tiêu</th>${P.map(p => `<th class="n">${E(p.id)}<br><span class="small mute" style="font-weight:400;text-transform:none">đến ${dmy(p.end)}</span></th>`).join("")}${P.length > 1 ? '<th class="n">So kỳ trước</th>' : ""}${P.length > 1 ? "<th>Xu hướng</th>" : ""}</tr>`;
  const body = ROWS.map(([n, fn, k, tr]) => { const vals = P.map(fn);
   return `<tr><td class="l">${E(n)}</td>${vals.map(v => `<td class="n">${fmt(v, k)}</td>`).join("")}${P.length > 1 ? `<td class="n">${delta(vals[0], vals[1], k)}</td>` : ""}${P.length > 1 ? `<td>${tr ? trendSvg([...vals].reverse(), n) : ""}</td>` : ""}</tr>`; }).join("");
  return `<div class="small mute" style="margin-top:6px">Đơn vị: tỷ đồng, trừ khi ghi %, ngày hoặc lần. Trên điện thoại: vuốt ngang để xem hết cột.</div><div class="tw"><table class="t"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
 };
 const newsFor = u => { const seen = new Set(), L = [];
  for (const x of (mk?.items || [])) if (x.org === u.org && x.org_type) L.push({t: x.title, u: x.sources?.[0]?.url, d: x.date, s: x.sources?.[0]?.name || "", ed: 1, txt: x.title + " " + (x.summary || "")});
  for (const x of (fd?.items || [])) if (x.org === u.org && x.org_type) L.push({t: x.title, u: x.url, d: x.date, s: x.source || "", ed: 0, txt: x.title});
  return L.filter(x => x.u && !seen.has(x.u) && seen.add(x.u)).map(x => ({...x, risk: RISK.test(HUB.strip(x.txt)) && !NOISE.test(HUB.strip(x.txt))})).sort((a, b) => (b.d || "").localeCompare(a.d || ""));
 };
 const flagsFor = (u, news) => {
  const F = [...u.flags]; const f = u.fin;
  if (f) { F.push(...f.flags);
   const age = dayDiff(f.periods[0].end); if (age > D.old_period_days) F.push({sev: "warn", t: "Kỳ báo cáo đã cũ", d: `Số liệu mới nhất kết thúc ngày ${dmy(f.periods[0].end)} (cách đây ${age} ngày) – tình hình hiện tại có thể đã khác.`});
   if (f.newer) F.push({sev: "warn", t: "Đã có BCTC mới hơn chưa đưa vào bảng", d: `<a href="${E(f.newer.url)}" target="_blank" rel="noopener">${E(f.newer.label)} ↗</a> – chưa được kiểm chứng trong bảng này, nên nhãn bên cạnh dựa trên kỳ cũ hơn.`, html: 1});
   const fa = dayDiff(f.verified_on); if (fa > D.stale_days) F.push({sev: "warn", t: "Số liệu BCTC đã quá hạn cập nhật", d: `Kiểm chứng ngày ${dmy(f.verified_on)} (${fa} ngày trước, hạn ${D.stale_days} ngày).`}); }
  const ra = dayDiff(u.reg.fetched); if (ra > D.stale_days) F.push({sev: "warn", t: "Thông tin đăng ký đã quá hạn cập nhật", d: `Lấy ngày ${dmy(u.reg.fetched)} (${ra} ngày trước).`});
  const nr = news.filter(x => x.risk).length; if (nr) F.push({sev: "warn", t: `${nr} tin gần đây có từ khóa rủi ro`, d: "Tiêu đề chứa từ như nợ thuế, vi phạm, tranh chấp, thua lỗ… (lọc theo từ khóa, chưa kiểm chứng). Xem mục “Tin gần đây”."});
  const ord = {bad: 0, warn: 1, info: 2}; return F.sort((a, b) => ord[a.sev] - ord[b.sev]);
 };
 const labelBox = u => {
  const f = u.fin;
  if (!f) return `<div class="ncc-box"><h4>Nhãn sức khỏe tài chính</h4><span class="ncc-sig unl">${u.ticker ? "Chưa có số liệu đã kiểm chứng" : "Chưa có BCTC công khai"}</span>
   <p class="small" style="margin:8px 0 0">${u.ticker ? E(u.short) + " đã niêm yết (" + E(u.ticker) + ") nhưng bảng này chưa nhập số liệu BCTC đã kiểm chứng, nên" : E(u.short) + " chưa niêm yết (hoặc không công bố báo cáo tài chính trong nguồn hub theo dõi) nên"} bảng <b>không có doanh thu, lợi nhuận hay nợ</b> và <b>không ước lượng</b>. ${u.ticker ? "Xem BCTC gốc trên trang công bố thông tin của công ty hoặc của sàn." : "Hãy yêu cầu đơn vị cung cấp BCTC kiểm toán mới nhất."}</p>${u.note ? `<p class="small mute" style="margin:6px 0 0">${E(u.note)}</p>` : ""}</div>`;
  const L = f.label, p0 = f.periods[0];
  const items = [...L.items].sort((a, b) => b.pts - a.pts);
  const rules = D.rules.map(r => { const it = L.items.find(x => x.id === r.id); return `<tr><td class="l"><b>${E(r.short)}</b><br><span class="small mute">${E(r.name)}</span></td><td class="l">${E(r.tiers)}</td><td class="l">${it ? E(it.val) : "–"}</td><td class="n">${it && it.status !== "na" ? it.pts : "–"}</td></tr>`; }).join("");
  return `<div class="ncc-box"><h4>Nhãn sức khỏe tài chính</h4><span class="ncc-sig ${L.k}">${LAB[L.k]}</span>${L.pts != null ? `<span class="ncc-pts">${L.pts} điểm · dựa trên ${E(p0.label)}</span>` : ""}
   <ul class="ncc-why">${items.map(i => `<li><span class="pt ${i.status}">${i.status === "na" ? "–" : i.pts ? "+" + i.pts : "0"}</span><span${i.pts ? "" : ' class="mute"'}>${E(i.say)}</span></li>`).join("")}</ul>
   <details><summary>Cách tính nhãn (ngưỡng công khai)</summary>
    <p class="small" style="margin:6px 0 0">Mỗi chỉ tiêu chạm ngưỡng được cộng điểm; tổng điểm: ${D.bands.map(b => `<b>${E(b.label)}</b> ${E(b.pts)}`).join(" · ")}. Không đủ số liệu cốt lõi → “Chưa đủ dữ liệu”.</p>
    <div class="tw"><table class="t"><thead><tr><th class="l">Chỉ tiêu</th><th class="l">Ngưỡng cộng điểm</th><th class="l">Kỳ này</th><th class="n">Điểm</th></tr></thead><tbody>${rules}</tbody></table></div>
    <p class="small mute" style="margin:6px 0 0">${D.rules.map(r => `<b>${E(r.short)}:</b> ${E(r.desc)}`).join("<br>")}</p></details>
   <div class="ncc-disc">${E(D.disclaimer)}</div></div>`;
 };
 const card = u => {
  const f = u.fin, news = newsFor(u), F = flagsFor(u, news), r = u.reg;
  const info = `<div class="ncc-box"><h4>Thông tin doanh nghiệp</h4><dl>
   <dt>Tên pháp nhân</dt><dd><b>${E(r.legal)}</b></dd><dt>Mã số thuế</dt><dd>${E(u.mst)}</dd>
   <dt>Tình trạng thuế</dt><dd><span class="pill ${r.active ? "hcm" : "hn"}">${r.active ? "✓ " : "⚠ "}${E(r.status)}</span></dd>
   <dt>Địa chỉ</dt><dd>${E(r.address)}</dd>${u.ticker ? `<dt>Mã chứng khoán</dt><dd><b>${E(u.ticker)}</b> · ${E(u.exchange)}</dd>` : '<dt>Niêm yết</dt><dd>Chưa niêm yết / không có BCTC công khai</dd>'}
   ${u.group ? `<dt>Nhóm</dt><dd>${E(u.group)}</dd>` : ""}${u.website ? `<dt>Website</dt><dd><a href="${E(u.website)}" target="_blank" rel="noopener">${E(u.website.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, ""))} ↗</a></dd>` : ""}
   <dt>Nguồn</dt><dd>${E(r.source)} · lấy ngày ${dmy(r.fetched)}${r.upstream_updated ? ` · gốc cập nhật ${dmy(r.upstream_updated)}` : ""} · <a href="${E(r.url)}" target="_blank" rel="noopener">bản ghi gốc ↗</a></dd></dl>
   ${u.note ? `<p class="small mute" style="margin:6px 0 0">${E(u.note)}</p>` : ""}</div>`;
  const warn = `<div class="ncc-box"><h4>Cảnh báo</h4>${F.length ? `<ul class="ncc-flags">${F.map(x => `<li class="${x.sev}"><span aria-hidden="true">${SEV[x.sev]}</span><span><b>${E(x.t)}</b>${x.html ? x.d : E(x.d)}</span></li>`).join("")}</ul>` : '<p class="small" style="margin:0">Chưa có cờ nào từ số liệu bảng này đang theo dõi. <b>Không có nghĩa là không có rủi ro</b> – hãy làm các bước ở mục “Việc buyer nên làm tiếp”.</p>'}</div>`;
  const fin = f ? `<div class="ncc-sec"><h4>Tài chính ${E(f.basis.toLowerCase())} – ${f.periods.length} kỳ, ${E(f.periods[0].audit.toLowerCase())}</h4>${finTable(f)}
   <p class="ncc-note">Kỳ báo cáo: ${f.periods.map(p => E(p.label)).join("; ")}. ${f.fy_note ? E(f.fy_note) + ". " : ""}${f.note ? E(f.note) + " " : ""}Kiểm toán: ${E(f.auditor)}. Đã kiểm chứng ngày ${dmy(f.verified_on)}: đọc tay từ PDF gốc, kiểm phép cộng trừ (tổng tài sản = nợ + vốn chủ; doanh thu − giá vốn = lợi nhuận gộp)${f.periods.some(p => p.xref) ? "; kỳ " + f.periods.filter(p => p.xref).map(p => E(p.id)).join(", ") + " trùng khớp giữa 2 BCTC độc lập" : ""}. Số ngày thu tiền = phải thu khách hàng ÷ doanh thu × số ngày của kỳ.</p>
   <p class="ncc-note">${f.periods.flatMap(p => p.notes.map(n => E(p.id) + ": " + E(n))).join(" ")}</p>
   <p class="ncc-note"><b>BCTC gốc:</b> ${f.periods.map(p => `<a href="${E(p.source.url)}" target="_blank" rel="noopener">${E(p.id)} – ${E(p.source.title)}${p.source.pages ? " (" + E(p.source.pages) + ")" : ""} ↗</a>`).filter((x, i, a) => a.indexOf(x) === i).join(" · ")}${f.ir_url ? ` · <a href="${E(f.ir_url)}" target="_blank" rel="noopener">trang cổ đông của công ty ↗</a>` : ""}</p></div>`
   : `<div class="ncc-sec"><h4>Tài chính</h4><p class="small" style="margin:0"><b>${u.ticker ? "Chưa có số liệu đã kiểm chứng" : "Chưa có BCTC công khai"}</b> trong nguồn hub dùng – bảng không hiển thị doanh thu/lợi nhuận và không ước lượng.</p></div>`;
  const nw = `<div class="ncc-sec"><h4>Tin gần đây về đơn vị</h4>${news.length ? `<ul class="ncc-news">${news.slice(0, 6).map(x => `<li><a href="${E(x.u)}" target="_blank" rel="noopener">${E(x.t)}</a> <span class="small mute">${HUB.date(x.d)}${x.s ? " · " + E(x.s) : ""}</span><span class="ncc-tag">${x.ed ? "tin biên tập" : "tự động"}</span>${x.risk ? '<span class="ncc-tag risk">từ khóa rủi ro</span>' : ""}</li>`).join("")}</ul>` : '<p class="small mute" style="margin:0">Chưa có tin nào gắn với đơn vị này trong 30 ngày qua.</p>'}
   <p class="ncc-note">Tin tự động lấy từ Google News theo tên đơn vị là <b>tin chưa kiểm chứng</b>, có thể lẫn tin không liên quan; “từ khóa rủi ro” chỉ là lọc chữ trong tiêu đề. <a href="nha-thau.html?org=${encodeURIComponent(u.org)}">Xem toàn bộ tin về ${E(u.short)} ↗</a></p></div>`;
  const todo = `<div class="ncc-sec"><h4>Việc buyer nên làm tiếp</h4><ol class="ncc-todo">
   <li><b>Đối chiếu tên pháp nhân + MST</b> với hợp đồng/giấy đăng ký: <a href="${E(D.links[0].u)}" target="_blank" rel="noopener">Cổng tra MST của Tổng cục Thuế ↗</a> <span class="ncc-tag">chưa tra tự động</span></li>
   <li><b>Xem hồ sơ đăng ký</b> (vốn điều lệ, người đại diện, ngành, thay đổi): <a href="${E(D.links[1].u)}" target="_blank" rel="noopener">Cổng đăng ký doanh nghiệp quốc gia ↗</a> <span class="ncc-tag">chưa tra tự động</span></li>
   <li><b>Kiểm tra nhà thầu bị xử lý vi phạm / kết quả thầu</b> trên <a href="${E(D.links[2].u)}" target="_blank" rel="noopener">muasamcong ↗</a> (tìm theo MST ${E(u.mst)}) <span class="ncc-tag">chưa tra tự động</span></li>
   <li><b>Tra doanh nghiệp rủi ro về hóa đơn / nợ thuế</b> do cơ quan thuế công bố: <a href="${E(D.links[3].u)}" target="_blank" rel="noopener">Tổng cục Thuế ↗</a> <span class="ncc-tag">chưa tra tự động</span></li>
   ${f ? `<li><b>Mở BCTC gốc</b> ở mục trên và đọc thuyết minh về công nợ, nợ vay, cam kết/bảo lãnh${f.newer ? `; có bản mới hơn: <a href="${E(f.newer.url)}" target="_blank" rel="noopener">${E(f.newer.label)} ↗</a>` : ""}.</li>` : `<li><b>Yêu cầu đơn vị cung cấp</b> BCTC kiểm toán mới nhất, danh sách hợp đồng đang thực hiện và thư bảo lãnh ngân hàng trước khi cấp tạm ứng.</li>`}</ol>
   <p class="ncc-note">Các mục 1–4 <b>chưa được tra tự động</b> – bảng này không thể và không khẳng định đơn vị “không có vi phạm”.</p></div>`;
  const cmpBox = `<div class="ncc-cmp"><label for="ncc-cmp-sel"><b>So sánh nhanh</b> với (tối đa 2):</label><select id="ncc-cmp-sel" ${cmp.length >= 2 ? "disabled" : ""}><option value="">— chọn đơn vị —</option>${U.filter(x => x.id !== u.id && !cmp.includes(x.id)).sort((a, b) => b.listed - a.listed || a.org.localeCompare(b.org, "vi")).map(x => `<option value="${x.id}">${E(x.short)}${x.ticker ? " (" + E(x.ticker) + ")" : ""}</option>`).join("")}</select>
   ${cmp.map(id => `<span class="chip on">${E(BY[id].short)}<button type="button" data-rm="${id}" aria-label="Bỏ ${E(BY[id].short)} khỏi so sánh">✕</button></span>`).join("")}</div>${cmp.length ? cmpTable(u) : ""}`;
  return `<article class="ncc-card" aria-label="Hồ sơ ${E(u.short)}"><div class="ncc-top"><div><h3>${E(r.legal)}</h3><div>${u.ticker ? `<span class="pill cat">${E(u.ticker)} · ${E(u.exchange)}</span>` : '<span class="pill">Chưa niêm yết</span>'}<span class="pill">MST ${E(u.mst)}</span>${u.group ? `<span class="pill">${E(u.group)}</span>` : ""}</div></div>
   <span class="small mute">Dữ liệu dựng sẵn · ${f ? "BCTC kiểm chứng " + dmy(f.verified_on) + " · " : ""}đăng ký lấy ${dmy(r.fetched)}</span></div>
   <div class="ncc-grid">${info}${labelBox(u)}${warn}</div>${fin}${nw}${todo}${cmpBox}</article>`;
 };
 const cmpTable = u => {
  const ids = [u.id, ...cmp], Us = ids.map(id => BY[id]);
  const row = (n, fn) => `<tr><td class="l">${n}</td>${Us.map(x => `<td class="n" style="white-space:normal">${x.fin ? fn(x.fin.periods[0], x.fin) : `<span class="mute">${x.ticker ? "Chưa có số liệu đã kiểm chứng" : "Chưa có BCTC công khai"}</span>`}</td>`).join("")}</tr>`;
  return `<div class="tw" style="margin-top:8px"><table class="t"><thead><tr><th class="l">Chỉ tiêu (kỳ mới nhất đã kiểm chứng)</th>${Us.map(x => `<th class="n">${E(x.short)}</th>`).join("")}</tr></thead><tbody>
   <tr><td class="l">Nhãn sức khỏe</td>${Us.map(x => `<td class="n">${x.fin ? `<span class="ncc-sig ${x.fin.label.k}" style="font-size:12.5px;padding:2px 9px">${LAB[x.fin.label.k]}</span> <span class="small mute">${x.fin.label.pts ?? ""} đ</span>` : `<span class="ncc-sig unl" style="font-size:12px;padding:2px 9px">${x.ticker ? "Chưa có số liệu đã kiểm chứng" : "Chưa có BCTC công khai"}</span>`}</td>`).join("")}</tr>
   ${row("Kỳ báo cáo", p => E(p.id))}${row("Doanh thu (tỷ)", p => T(p.v.rev))}${row("LNST (tỷ)", p => T(p.v.np))}${row("Biên lợi nhuận ròng", p => PC(p.m.nm))}${row("Nợ vay ÷ vốn chủ", p => X(p.m.dbe))}${row("Thanh khoản hiện hành", p => X(p.m.cr))}${row("Số ngày thu tiền", p => X(p.m.dso, 0))}${row("Dòng tiền kinh doanh (tỷ)", p => T(p.v.cfo))}
   <tr><td class="l">Tình trạng thuế</td>${Us.map(x => `<td class="n" style="white-space:normal">${x.reg.active ? "✓ " : "⚠ "}${E(x.reg.status)}</td>`).join("")}</tr></tbody></table></div><p class="ncc-note">So sánh các kỳ có thể khác nhau (Coteccons dùng năm tài chính 01/07–30/06; các công ty khác dùng năm dương lịch).</p>`;
 };
 const render = () => {
  if (!cur) { out.innerHTML = ""; return; }
  out.innerHTML = card(cur);
  const sel = document.getElementById("ncc-cmp-sel"); if (sel) sel.onchange = () => { if (sel.value && cmp.length < 2) { cmp.push(sel.value); render(); document.getElementById("ncc-cmp-sel")?.focus(); } };
  out.querySelectorAll("[data-rm]").forEach(b => b.onclick = () => { cmp = cmp.filter(x => x !== b.dataset.rm); render(); document.getElementById("ncc-cmp-sel")?.focus(); });
 };
 const q0 = HUB.qs("ncc"); if (q0) { const r = find(q0); if (r.length) pick(r[0].id); else { inp.value = q0; notFound(q0); } }
})();
