"""Sinh icon PWA 'SCM' (không dùng logo/thương hiệu nào): python tools/make_pwa_icons.py
Màu lấy từ hub: nền #0e1a2b (thanh nav), chữ trắng, vạch nhấn #b08d57 (viền vàng của thanh nav).
Ra trends/web/: scm-icon-192.png, scm-icon-512.png (any, bo góc), scm-icon-maskable-512.png (full-bleed, chữ trong vùng an toàn 80%),
scm-apple-touch-180.png (vuông đặc, iOS tự bo góc)."""
import os
from PIL import Image, ImageDraw, ImageFont
NAVY, GOLD, WHITE = (14, 26, 43), (176, 141, 87), (255, 255, 255)
FONT = next(p for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf") if os.path.exists(p))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trends", "web")
def draw(size, rounded, scale):
    S = size * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if rounded: d.rounded_rectangle((0, 0, S - 1, S - 1), radius=int(S * .2), fill=NAVY)
    else: d.rectangle((0, 0, S, S), fill=NAVY)
    f = ImageFont.truetype(FONT, int(S * .34 * scale)); t = "SCM"
    b = d.textbbox((0, 0), t, font=f); w, h = b[2] - b[0], b[3] - b[1]
    bar_h, gap = int(S * .022 * scale), int(S * .045 * scale); tot = h + gap + bar_h
    y0 = (S - tot) // 2; x0 = (S - w) // 2 - b[0]
    d.text((x0, y0 - b[1]), t, font=f, fill=WHITE)
    by = y0 + h + gap; d.rectangle(((S - w) // 2, by, (S + w) // 2, by + bar_h), fill=GOLD)
    return im.resize((size, size), Image.LANCZOS)
for name, size, rounded, scale in (("scm-icon-192.png", 192, True, 1), ("scm-icon-512.png", 512, True, 1), ("scm-icon-maskable-512.png", 512, False, .74), ("scm-apple-touch-180.png", 180, False, 1)):
    im = draw(size, rounded, scale)
    if not rounded: im = im.convert("RGB")
    im.save(os.path.join(OUT, name), optimize=True); print(name, im.size, im.mode)
