/* Service worker tối thiểu cho SCM Hub (PWA). Mục tiêu: luôn thấy dữ liệu mới nhất khi có mạng.
   - HTML, JSON dữ liệu, css/js: MẠNG TRƯỚC (kèm revalidate cache:'no-cache'), chỉ dùng bản đã lưu khi mất mạng/quá chậm.
   - icon/manifest/ảnh/font: cache-first (gần như bất biến).
   - Không đụng /api, không đụng yêu cầu khác nguồn (goatcounter...), không đụng non-GET.
   VERSION do trends/build.py đóng dấu theo nội dung tài nguyên tĩnh; đổi → cache cũ bị xoá khi kích hoạt. */
const VERSION = "__SW_VERSION__";
const CACHE = "scm-hub-" + VERSION;
const SHELL = ["./", "index.html", "hub.css", "hub-nav.css", "hub-common.js", "manifest.webmanifest", "scm-icon-192.png", "scm-icon-512.png", "scm-apple-touch-180.png"];
const NET_TIMEOUT = 8000;

self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await Promise.all(SHELL.map(u => fetch(u, {cache: "reload"}).then(r => r.ok && c.put(u, r)).catch(() => {})));
    await self.skipWaiting();
  })());
});
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith("scm-hub-") && k !== CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});

const key = url => { const u = new URL(url); u.search = ""; u.hash = ""; return u.href; };  // bỏ ?query để cache không phình
const isStaticAsset = p => /\.(png|svg|ico|webp|jpg|jpeg|woff2?|webmanifest)$/i.test(p);

async function networkFirst(req) {
  const c = await caches.open(CACHE), k = key(req.url);
  const net = fetch(req.url, {cache: "no-cache", credentials: "same-origin"}).then(async r => {
    if (r.redirected) r = new Response(await r.blob(), {status: r.status, statusText: r.statusText, headers: r.headers});  // trang điều hướng không được trả response đã redirect
    if (r.ok) c.put(k, r.clone());
    return r;
  });
  const cached = await c.match(k);
  if (!cached) return net;  // chưa có bản lưu: chờ mạng bình thường
  try {
    return await Promise.race([net, new Promise((_, rej) => setTimeout(() => rej(new Error("slow")), NET_TIMEOUT))]);
  } catch (err) { net.catch(() => {}); return cached; }  // mất mạng hoặc quá chậm → bản đã lưu
}
async function cacheFirst(req) {
  const c = await caches.open(CACHE), k = key(req.url), hit = await c.match(k);
  if (hit) return hit;
  const r = await fetch(req); if (r.ok && r.type === "basic" && !r.redirected) c.put(k, r.clone());
  return r;
}
self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;       // khác nguồn / không phải GET: để trình duyệt tự xử lý
  if (url.pathname.startsWith("/api/") || req.headers.has("range")) return;        // không cache /api
  if (url.pathname === "/sw.js" || /\.(csv|xlsx|zip|pdf)$/i.test(url.pathname)) return;  // tải về file: không qua cache
  if (req.mode === "navigate") {
    e.respondWith(networkFirst(req).catch(async () => (await (await caches.open(CACHE)).match(key(new URL("index.html", self.location).href))) || new Response("Đang ngoại tuyến và trang này chưa được lưu. Kết nối mạng rồi mở lại.", {status: 503, headers: {"Content-Type": "text/plain; charset=utf-8"}})));
    return;
  }
  e.respondWith((isStaticAsset(url.pathname) ? cacheFirst(req) : networkFirst(req)).catch(() => fetch(req)));
});
