// SCM – Bảng so sánh landed cost Trung Quốc vs mua nội địa (data/landed-cost.json, built by trends/landed.py)
(async () => {
 const box = document.getElementById("lcbox"); if (!box) return;
 const d = await HUB.get("landed-cost.json"); const E = HUB.esc;
 if (!d) { box.innerHTML = '<div class="empty">Không tải được dữ liệu landed cost (data/landed-cost.json).</div>'; return; }
 const st = document.createElement("style"); st.textContent = `.lc-asm{display:inline-block;background:#fff4e5;color:#8a5a00;border:1px solid #f0d9b5;border-radius:6px;font-size:11px;padding:0 5px;font-weight:600}
 .lc-t td,.lc-t th{vertical-align:top}.lc-t .nm{min-width:190px}.lc-t .vd{white-space:nowrap}.lc-det td{background:#fafbfc}.lc-det td>.lc-kv{will-change:transform}.lc-det .calc{margin-top:4px}
 .lc-kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:12px}.lc-kv>div{min-width:0}.lc-kv h4{margin:6px 0 4px;font-size:14px}
 .lc-src a{word-break:break-word}.lc-btn{font:inherit;font-size:12.5px;padding:4px 9px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer;color:var(--pri);white-space:nowrap}
 .lc-btn:hover{background:var(--pri2)}.lc-sv{font-weight:700}.lc-note{font-size:12.5px;color:var(--mute)}.lc-sec h3{margin-top:14px}
 .lc-ctl{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;margin-bottom:10px}.lc-ctl label{display:flex;flex-direction:column;font-size:12.5px;color:var(--mute);gap:3px}
 .lc-ctl input,.lc-ctl select{padding:7px 9px;border:1px solid var(--line);border-radius:10px;font:inherit;font-size:14px;width:130px;background:#fff;color:var(--ink)}
 .lc-det table.t{min-width:0}.lc-mini td,.lc-mini th{padding:4px 8px}`;
 document.head.appendChild(st);
 const VD = {"co-hoi": ["Cơ hội nhập khẩu", "#1e8449"], "can-nhac": ["Cân nhắc", "#b7791f"], "noi-dia": ["Mua nội địa", "#667085"]};
 const vb = v => `<span class="sig" style="background:${VD[v][1]}">${VD[v][0]}</span>`;
 const f0 = v => Math.round(v).toLocaleString("vi-VN"), pc = v => (v * 100).toLocaleString("vi-VN", {maximumFractionDigits: 1}) + "%";
 const fmtU = (v, u) => u === "Wp" ? v.toLocaleString("vi-VN", {maximumFractionDigits: 0}) : f0(v);
 const src = a => (a || []).map(s => `<a href="${E(s.url)}" target="_blank" rel="noopener">${E(s.name)}${s.date ? " (" + E(s.date) + ")" : ""} ↗</a>`).join(" · ");
 const KEY = "lc-ov-v1"; let ov = {}; try { ov = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { ov = {}; }
 const save = () => { try { localStorage.setItem(KEY, JSON.stringify(ov)); } catch (e) {} };
 let reg = HUB.qs("r") === "hcm" ? "hcm" : "hn", fx = d.fx.usd_vnd, fm = 1, sort = "sv-desc", vf = "", open = new Set();
 // per-item editable parameters (defaults from JSON)
 const P = it => { const o = ov[it.id] || {}; const t = it.tax; const rate = Math.min(...[t.mfn, t.acfta].filter(x => x != null));
  return {fob: o.fob ?? it.fob.mid, qty: o.qty ?? it.qty.v, duty: o.duty ?? rate, ad: o.ad ?? (it.ad_pct || 0), disc: o.disc ?? it.disc.v, local: o.local ?? it.local.mid,
   extra: o.extra ?? it.extra.v, brk: o.brk ?? it.breakage.v, insp: o.insp ?? it.inspect.v, lead: o.lead ?? it.lead.v}; };
 // SAME formula as trends/landed.py compute()
 function C(it, p, o = {}) { const X = o.fx ?? fx, k = "d" + it.cont.replace(/\D/g, ""), q = Math.max(p.qty, 1), fob = o.fob ?? p.fob;
  const fr = d.freight[reg][k] * (o.fm ?? fm) / q, ins = (fob + fr) * d.ins_pct.v / 100, cif = fob + fr + ins, duty = cif * p.duty / 100, ad = cif * p.ad / 100;
  const base = (cif + duty + ad) * X, port = (d.port.thc_usd[k] * X + d.port.do_vnd + d.port.broker_vnd + p.insp) / q, truck = d.truck[reg][k] / q;
  const brk = base * p.brk / 100, fin = base * d.fin_pct.v / 100 * p.lead / 365, landed = base + port + truck + brk + fin + p.extra;
  const lm = o.local ?? p.local, lex = (it.local.vat_incl ? lm / (1 + it.tax.vat / 100) : lm) * (1 - p.disc / 100) + d.local_delivery.v;
  return {fob: fob * X, fr: fr * X, ins: ins * X, cif: cif * X, duty: duty * X, ad: ad * X, port, truck, brk, fin, extra: p.extra, landed, vat: (cif + duty + ad) * X * it.tax.vat / 100, lex, sv: 1 - landed / lex}; }
 const V = s => s * 100 >= d.thresholds.opp ? "co-hoi" : s * 100 >= d.thresholds.consider ? "can-nhac" : "noi-dia";
 const fxNote = `Tỷ giá ${f0(d.fx.usd_vnd)} đ/USD · ${f0(d.fx.cny_vnd)} đ/CNY (${E(d.fx.text || "")}, ${E((d.fx.asof || "").replace("T", " "))})`;
 box.innerHTML = `<div class="lc-ctl"><span class="seg" id="lc-reg" aria-label="Khu vực công trình"><button data-r="hn">Hà Nội (cảng Hải Phòng)</button><button data-r="hcm">TP.HCM (cảng Cát Lái)</button></span>
  <label>Tỷ giá (đ/USD)<input id="lc-fx" type="number" step="any" min="1" value="${fx}"></label>
  <label>Hệ số cước biển (×)<input id="lc-fm" type="number" step="0.1" min="0" value="1"></label>
  <label>Sắp xếp<select id="lc-sort"><option value="sv-desc">Tiết kiệm cao → thấp</option><option value="sv-asc">Tiết kiệm thấp → cao</option><option value="grp">Theo nhóm</option></select></label>
  <span class="seg" id="lc-vf" aria-label="Lọc kết luận"><button data-v="" class="on">Tất cả</button>${Object.keys(VD).map(k => `<button data-v="${k}">${VD[k][0]}</button>`).join("")}</span>
  <button class="lc-btn" id="lc-reset" type="button">↺ Khôi phục giả định gốc</button></div>
  <div class="grid g3 kpis" id="lc-kpi"></div>
  <div class="tw" style="max-height:none;margin-top:10px"><table class="t lc-t" id="lc-tbl"></table></div>
  <p class="lc-note">${fxNote}. Cước biển: ${E(d.freight.note)} Nguồn: ${src([d.freight.src])}${d.freight.stale ? ' · <b class="up">cước đã cũ hơn 45 ngày – cần cập nhật</b>' : ""}. Phí cảng: THC ${d.port.thc_usd.d20}/${d.port.thc_usd.d40} USD (20'/40'), D/O ${f0(d.port.do_vnd)} đ, khai hải quan ${f0(d.port.broker_vnd)} đ/tờ khai – ${src(d.port.src)}. Vận chuyển nội địa: ${E(d.truck.hn.text)}; ${E(d.truck.hcm.text)} – ${src(d.truck.src)}. Bảo hiểm ${d.ins_pct.v}% <span class="lc-asm">GIẢ ĐỊNH</span>, chi phí vốn ${d.fin_pct.v}%/năm <span class="lc-asm">GIẢ ĐỊNH</span>. ${E(d.thresholds.text)} Thay đổi ô nhập được lưu trên trình duyệt này.</p>
  <h3>Nhóm chưa đủ dữ liệu giá (đã tra thuế) – cần RFQ</h3>
  <div class="tw" style="max-height:none"><table class="t"><tr><th>Nhóm</th><th>Mã HS</th><th class="n">MFN</th><th class="n">ACFTA (Form E)</th><th>Phòng vệ thương mại</th><th>Ghi chú</th></tr>${d.gaps.map(g => `<tr><td><b>${E(g.group)}</b></td><td>${E(g.hs)}</td><td class="n">${g.mfn ?? "–"}${g.mfn != null ? "%" : ""}</td><td class="n">${g.acfta ?? "–"}${g.acfta != null ? "%" : ""}</td><td class="small">${E(g.ad)}</td><td class="small">${E(g.note)}</td></tr>`).join("")}</table></div>
  <p class="lc-note">Nguồn thuế: ${src(d.tax_sources)}. Thuế PVTM: <a href="hop-dong.html">trang Hợp đồng → Thuế quan & phòng vệ thương mại</a>.</p>
  <div class="lc-sec">${METH()}</div>`;
 function METH() { return `<h3 id="lc-method">Phương pháp tính</h3><ol class="small">
  <li><b>Cùng tier:</b> mỗi dòng mô tả tier chất lượng/thẩm mỹ; giá FOB Trung Quốc lấy từ listing (Made-in-China, Tradewheel, BuildMost…) hoặc chỉ số ngành (InfoLink), giá nội địa từ bảng giá nhà phân phối/hãng cùng tier. Dùng <b>giá giữa</b> khoảng; cột “khoảng” dùng FOB cao + giá nội địa thấp (xấu nhất) và ngược lại.</li>
  <li><b>CIF</b> = FOB + cước biển/đơn vị (cước container ÷ số đơn vị/container theo thể tích hoặc tải trọng) + bảo hiểm.</li>
  <li><b>Thuế nhập khẩu</b> = CIF × min(MFN, ACFTA) – Form E chỉ dùng khi thấp hơn MFN (một số dòng ACFTA 50% cao hơn MFN). Cộng thuế chống bán phá giá/tự vệ nếu áp cho hàng TQ. Hiện không có thuế TTĐB cho các nhóm trong bảng.</li>
  <li><b>Chi phí tại VN</b> = (THC + D/O + khai hải quan + kiểm tra chuyên ngành/hợp quy theo lô) ÷ số đơn vị + vận chuyển container cảng → công trình ÷ số đơn vị + hao hụt/vỡ (% giá sau thuế) + chi phí vốn (% năm × lead time) + chi phí bổ sung để tương đương (vd. lắp đặt).</li>
  <li><b>Giá nội địa chưa VAT</b> = giá tham khảo ÷ (1 + VAT) nếu giá đã gồm VAT, × (1 − chiết khấu dự án giả định). Cả hai bên so sánh <b>chưa VAT</b> vì VAT nhập khẩu (tính trên CIF + thuế NK + CBPG) và VAT đầu vào nội địa đều được khấu trừ; VAT 8% theo NQ 204/2025/QH15 đến 31/12/2026 (10% với hàng không được giảm, ví dụ một số hàng điện tử, khóa).</li>
  <li><b>Tiết kiệm</b> = 1 − landed ÷ giá nội địa. Độ nhạy: tỷ giá ±5%, cước biển ×2.</li></ol>
  <h3 id="lc-ops">Cách triển khai (vận hành hóa)</h3><ol class="small">
  <li><b>Chốt spec & tier:</b> lập bảng thông số tương đương (kích thước, độ hút nước, PEI, độ phẳng; lớp mạ, lõi van; CRI, quang thông, driver…) và xin chủ đầu tư/thiết kế chấp thuận “tương đương” trước khi RFQ.</li>
  <li><b>RFQ 3–5 nhà máy</b> (không qua trader) trên Made-in-China/Alibaba/1688 & hội chợ Canton/Foshan; yêu cầu báo giá FOB + bảng đóng gói (pcs/thùng, kg, CBM, số lượng/cont), MOQ, lead time, chứng nhận (CE/ISO/CB), mã HS khai báo.</li>
  <li><b>Mẫu & đánh giá nhà máy:</b> nhận mẫu thật, thử nghiệm tại phòng thí nghiệm VN theo QCVN/TCVN (vd. QCVN 16:2023/BXD cho gạch, sứ vệ sinh, kính); audit nhà máy (video/bên thứ ba).</li>
  <li><b>Hợp đồng:</b> Incoterms FOB/CIF, thanh toán 30/70 hoặc L/C, điều khoản dung sai màu/lô, dự phòng 2–3% hàng thay thế, phạt chậm, bảo hành, và <b>bắt buộc C/O mẫu E</b> đúng mã HS (bản gốc giấy; hàng quá cảnh Hong Kong cần xác nhận không thay đổi xuất xứ).</li>
  <li><b>Kiểm tra trước xuất hàng (PSI)</b> AQL 2.5 bởi bên thứ ba; ảnh/clip đóng cont; đối chiếu packing list.</li>
  <li><b>Gom container:</b> ghép bàn cầu + lavabo + vòi; gạch nhiều mẫu cùng nhà máy/khu Foshan; dùng consolidator tại Foshan/Ningbo để tối ưu cước và chi phí cố định/lô.</li>
  <li><b>Thông quan:</b> khai đúng HS, nộp C/O E, đăng ký kiểm tra chuyên ngành/hợp quy trước khi hàng về; dự trù luồng vàng/đỏ.</li>
  <li><b>Tối ưu liên tục:</b> mỗi tháng cập nhật FX & cước (tự động), mỗi quý RFQ lại 1–2 nhóm và cập nhật giá nội địa; ghi giá thực tế về kho vào JSON (nguồn = PO/hóa đơn) để thay giả định; dùng giá landed làm <b>giá trần đàm phán</b> với nhà cung cấp nội địa.</li></ol>`; }
 function kpi(R) { document.getElementById("lc-kpi").innerHTML = Object.keys(VD).map(k => { const n = R.filter(r => r.v === k); return `<div class="tile"><b>${vb(k)}</b><div class="kpi">${n.length} <small>nhóm</small></div><div class="small">${n.map(r => E(r.it.name)).join(", ") || "–"}</div></div>`; }).join(""); }
 const FIELDS = [["fob", "FOB (USD/đv)"], ["qty", "Số đv/container"], ["duty", "Thuế NK áp dụng (%)"], ["ad", "Thuế CBPG/tự vệ (%)"], ["local", "Giá nội địa tham khảo (đ)"], ["disc", "Chiết khấu dự án nội địa (%)"], ["brk", "Hao hụt/vỡ (%)"], ["insp", "Kiểm tra/hợp quy (đ/lô)"], ["lead", "Lead time nhập (ngày)"], ["extra", "Chi phí bổ sung (đ/đv)"]];
 function det(it, p, c) { const t = it.tax, s5 = C(it, p, {fx: fx * 1.05}).sv, s95 = C(it, p, {fx: fx * .95}).sv, s2 = C(it, p, {fm: fm * 2}).sv, u = E(it.unit);
  const row = (l, v, b) => `<tr><td>${l}</td><td class="n">${b ? "<b>" : ""}${fmtU(v, it.unit)} đ${b ? "</b>" : ""}</td></tr>`;
  return `<tr class="lc-det"><td colspan="9"><div class="lc-kv">
   <div><h4>Giả định có thể chỉnh</h4><div class="calc">${FIELDS.map(([k, l]) => `<label>${l}<input data-id="${it.id}" data-k="${k}" type="number" step="any" min="0" value="${p[k]}"></label>`).join("")}</div>
    <div class="small">FOB: ${src(it.fob.src)}<br>Số đv/cont: ${E(it.qty.basis)}<br>Nội địa: ${E(it.local.what)} – ${src(it.local.src)}<br>Chiết khấu: <span class="lc-asm">GIẢ ĐỊNH</span> ${E(it.disc.basis)}<br>Hao hụt: ${E(it.breakage.basis)} · Hợp quy: ${E(it.inspect.basis)} · Lead time: ${E(it.lead.basis)}${it.extra.v ? "<br>Bổ sung: " + E(it.extra.basis) : ""}</div></div>
   <div><h4>Cấu phần giá về công trình (1 ${u}, chưa VAT)</h4><table class="t lc-mini">${row("FOB", c.fob)}${row("Cước biển phân bổ", c.fr)}${row("Bảo hiểm", c.ins)}${row("= CIF", c.cif, 1)}${row(`Thuế NK (${p.duty}%)`, c.duty)}${row(`Thuế CBPG/tự vệ (${p.ad}%)`, c.ad)}${row("Phí cảng + hải quan + hợp quy", c.port)}${row("Vận chuyển cảng → công trình", c.truck)}${row("Hao hụt/vỡ", c.brk)}${row("Chi phí vốn theo lead time", c.fin)}${c.extra ? row("Chi phí bổ sung", c.extra) : ""}${row("= Landed chưa VAT", c.landed, 1)}${row("VAT nhập khẩu (khấu trừ được)", c.vat)}${row("Giá nội địa chưa VAT, sau CK", c.lex, 1)}</table>
    <p class="small"><b>Độ nhạy tiết kiệm:</b> tỷ giá +5% → ${pc(s5)} · tỷ giá −5% → ${pc(s95)} · cước biển ×2 → ${pc(s2)}.</p>
    <p class="small"><button class="lc-btn" type="button" data-calc="${it.id}">→ Mở trong máy tính what-if (điền sẵn)</button></p></div>
   <div><h4>Thuế (mã HS ${E(t.hs)})</h4><p class="small">MFN ${t.mfn}% · ACFTA (Form E) ${t.acfta}% · CBPG: ${it.ad_pct ? it.ad_pct + "%" : "không áp với hàng TQ"} · TTĐB: không · VAT ${t.vat}%.<br>${E(t.note)}<br>${src(t.src)}</p>
    <h4>Yếu tố phi giá</h4><ul class="small"><li><b>Bảo hành:</b> ${E(it.np.warranty)}</li><li><b>MOQ:</b> ${E(it.np.moq)}</li><li><b>Lead time:</b> ${E(it.np.lead)}</li><li><b>Spec bàn giao/thương hiệu:</b> ${E(it.np.brand)}</li></ul>${it.conf_note ? `<p class="small"><b>Độ tin cậy ${E(it.conf)}:</b> ${E(it.conf_note)}</p>` : ""}</div></div></td></tr>`; }
 function render() { const R = d.items.map(it => { const p = P(it), c = C(it, p); return {it, p, c, v: V(c.sv), lo: C(it, p, {fob: it.fob.hi, local: it.local.lo}).sv, hi: C(it, p, {fob: it.fob.lo, local: it.local.hi}).sv}; });
  kpi(R); let L = R.filter(r => !vf || r.v === vf);
  L.sort(sort === "grp" ? (a, b) => a.it.group.localeCompare(b.it.group, "vi") : sort === "sv-asc" ? (a, b) => a.c.sv - b.c.sv : (a, b) => b.c.sv - a.c.sv);
  document.getElementById("lc-tbl").innerHTML = `<tr><th>Nhóm / mặt hàng (tier)</th><th>HS</th><th class="n">Thuế NK áp dụng</th><th class="n">FOB TQ (USD)</th><th class="n">Landed TQ chưa VAT</th><th class="n">Nội địa chưa VAT</th><th class="n">Tiết kiệm</th><th>Kết luận</th><th></th></tr>` +
   L.map(({it, p, c, v, lo, hi}) => { const t = it.tax, fe = t.acfta != null && t.acfta < t.mfn;
    return `<tr id="lc-${it.id}"><td class="nm"><span class="small mute">${E(it.group)}</span><br><b>${E(it.name)}</b><br><span class="small">${E(it.tier)}</span></td><td class="small">${E(t.hs)}</td>
     <td class="n small"><b>${p.duty}%</b><br>${fe ? `Form E (MFN ${t.mfn}%)` : `MFN (ACFTA ${t.acfta}%)`}${p.ad ? `<br>+CBPG ${p.ad}%` : ""}</td>
     <td class="n small">${it.fob.lo}–${it.fob.hi}<br><b>${p.fob}</b>/${E(it.unit)}</td><td class="n"><b>${fmtU(c.landed, it.unit)} đ</b><br><span class="small mute">/${E(it.unit)}</span></td>
     <td class="n">${fmtU(c.lex, it.unit)} đ<br><span class="small mute">CK ${p.disc}%</span></td>
     <td class="n"><span class="lc-sv ${c.sv >= 0 ? "down" : "up"}">${pc(c.sv)}</span><br><span class="small mute">khoảng ${pc(lo)} → ${pc(hi)}</span></td><td class="vd">${vb(v)}${it.conf ? `<br><span class="small mute">Độ tin cậy: <b>${E(it.conf)}</b></span>` : ""}</td>
     <td><button class="lc-btn" type="button" data-tg="${it.id}" aria-expanded="${open.has(it.id)}">${open.has(it.id) ? "Thu gọn ▴" : "Chi tiết ▾"}</button></td></tr>${open.has(it.id) ? det(it, p, c) : ""}`; }).join("") + (L.length ? "" : '<tr><td colspan="9" class="mute">Không có nhóm phù hợp.</td></tr>');
  box.querySelectorAll("[data-tg]").forEach(b => b.onclick = () => { const i = b.dataset.tg; open.has(i) ? open.delete(i) : open.add(i); render(); });
  box.querySelectorAll(".lc-det input").forEach(i => i.onchange = () => { const v = parseFloat(i.value); (ov[i.dataset.id] ||= {})[i.dataset.k] = isNaN(v) ? undefined : v; save(); render(); });
  box.querySelectorAll("[data-calc]").forEach(b => b.onclick = () => toCalc(b.dataset.calc)); fit(); }
 // keep the detail panel inside the visible width of the horizontally scrollable table (mobile)
 const tw = () => document.querySelector("#lcbox .tw");
 function fit() { const w = tw(); if (!w) return; const tbl = w.querySelector("table"), narrow = tbl.scrollWidth > w.clientWidth + 1;
  w.querySelectorAll(".lc-kv").forEach(k => { k.style.width = narrow ? (w.clientWidth - 26) + "px" : ""; k.style.transform = narrow ? `translateX(${w.scrollLeft}px)` : ""; }); }
 addEventListener("resize", fit);
 function toCalc(id) { const it = d.items.find(x => x.id === id), p = P(it), c = C(it, p), k = "d" + it.cont.replace(/\D/g, "");
  if (!window.HUB_CALC_SET) return; const logi = (c.port + c.truck + c.brk + c.fin + c.extra) / c.cif * 100;
  window.HUB_CALC_SET({fob: p.fob, qty: p.qty, frt: +(d.freight[reg][k] * fm).toFixed(0), ins: d.ins_pct.v, duty: p.duty, ad: p.ad, vat: it.tax.vat, logi: +logi.toFixed(4), fx, vn: Math.round(c.lex)},
   `Điền sẵn từ bảng so sánh: <b>${E(it.name)}</b> · đơn vị <b>${E(it.unit)}</b> · ${E(it.cont)} · ${reg === "hn" ? "Hà Nội (Hải Phòng)" : "TP.HCM (Cát Lái)"} · “Logistics nội địa + thông quan” = phí cảng, hải quan, hợp quy, vận chuyển, hao hụt, chi phí vốn${c.extra ? ", chi phí bổ sung" : ""} quy về % CIF · “Giá trong nước” = giá nội địa chưa VAT sau chiết khấu.`, it.unit); }
 const segOn = (id, attr, val) => document.querySelectorAll(`#${id} button`).forEach(b => b.classList.toggle("on", b.dataset[attr] === val));
 document.querySelectorAll("#lc-reg button").forEach(b => b.onclick = () => { reg = b.dataset.r; segOn("lc-reg", "r", reg); render(); }); segOn("lc-reg", "r", reg);
 document.querySelectorAll("#lc-vf button").forEach(b => b.onclick = () => { vf = b.dataset.v; segOn("lc-vf", "v", vf); render(); });
 document.getElementById("lc-fx").oninput = e => { fx = parseFloat(e.target.value) || d.fx.usd_vnd; render(); };
 document.getElementById("lc-fm").oninput = e => { const v = parseFloat(e.target.value); fm = isNaN(v) ? 1 : v; render(); };
 document.getElementById("lc-sort").onchange = e => { sort = e.target.value; render(); };
 document.getElementById("lc-reset").onclick = () => { ov = {}; save(); fx = d.fx.usd_vnd; fm = 1; document.getElementById("lc-fx").value = fx; document.getElementById("lc-fm").value = 1; render(); };
tw().addEventListener("scroll", fit, {passive: true});
 render(); if (location.hash === "#landed") document.getElementById("landed").scrollIntoView();
})();
