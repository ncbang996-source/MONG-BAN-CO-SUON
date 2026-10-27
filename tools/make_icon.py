"""Vẽ biểu tượng app: móng bản có dầm 3D (bản móng, 2 dầm mỗi phương, 4 cổ trụ, bu lông), nhìn trục đo."""
import math
import os

from PIL import Image, ImageDraw

SS = 8                 # vẽ to rồi thu nhỏ để mịn
SIZE = 48
W = SIZE * SS * 2
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
K = W / 10.8           # đơn vị -> pixel
OX, OY = W / 2, W * 0.7


def P(x, y, z):
    """Trục đo: x sang phải-xuống, y sang trái-xuống, z lên."""
    return (OX + (x - y) * C30 * K, OY + ((x + y) * S30 - z) * K)


def shade(base, f):
    return tuple(max(0, min(255, int(c * f))) for c in base) + (255,)


CON = (205, 208, 212)
EDGE = (88, 92, 100, 255)


def poly(d, pts, col):
    d.polygon([P(*p) for p in pts], fill=col, outline=EDGE, width=max(1, int(0.55 * SS)))


def box(d, x0, y0, z0, x1, y1, z1, col):
    poly(d, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], shade(col, 0.80))   # mặt trước-trái
    poly(d, [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], shade(col, 0.62))   # mặt trước-phải
    poly(d, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], shade(col, 1.06))   # mặt trên


PALETTES = {
    # tên: lót, bản móng, dầm, cổ móng, bu lông, nền (None = trong suốt)
    "xam": dict(lot=(150, 150, 150), slab=CON, rib=CON, pier=CON, bolt=(40, 40, 40), bg=None),
    "cam": dict(lot=(196, 164, 116), slab=(208, 211, 216), rib=(74, 134, 196), pier=(242, 142, 44),
                bolt=(35, 35, 35), bg=None),
    "xanh": dict(lot=(150, 140, 125), slab=(176, 206, 228), rib=(44, 96, 166), pier=(22, 158, 146),
                 bolt=(30, 30, 30), bg=None),
    "nen": dict(lot=(196, 164, 116), slab=(214, 217, 222), rib=(150, 186, 222), pier=(242, 142, 44),
                bolt=(25, 25, 25), bg=(31, 58, 95)),
    "am": dict(lot=(140, 120, 100), slab=(232, 204, 146), rib=(192, 84, 62), pier=(96, 104, 116),
               bolt=(30, 30, 30), bg=None),
}
PAL = "am"                # phương án D - tông ấm (đã chọn)


def draw(pal, size=SIZE):
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    L, hs, hb = 3.0, 0.3, 0.75            # nửa cạnh bản móng, dày bản, cao dầm
    box(d, -L - 0.25, -L - 0.25, -0.22, L + 0.25, L + 0.25, 0.0, pal["lot"])      # bê tông lót
    box(d, -L, -L, 0.0, L, L, hs, pal["slab"])                                    # bản móng
    w = 0.32                                                                      # nửa bề rộng dầm
    # hệ dầm 2 phương cao bằng nhau + vát nách tại chỗ giao: chia thành các khối, vẽ từ xa tới gần
    ts = (-1.3, 1.3)
    e = 0.36                                                                      # cạnh vát nách
    cuts = sorted({-L, L} | {t + s_ * v for t in ts for s_ in (-1, 1) for v in (w, w + e)})
    pieces = set()
    for t in ts:
        for i in range(len(cuts) - 1):
            pieces.add((t - w, cuts[i], t + w, cuts[i + 1]))     # dầm theo Y
            pieces.add((cuts[i], t - w, cuts[i + 1], t + w))     # dầm theo X
    tris = []                                                    # vát nách: tam giác ở 4 góc mỗi chỗ giao
    for tx in ts:
        for ty in ts:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    tris.append([(tx + sx * w, ty + sy * w), (tx + sx * (w + e), ty + sy * w),
                                 (tx + sx * w, ty + sy * (w + e))])
    items = [("b", q, q[2] + q[3]) for q in pieces] + [("t", q, max(x + y for x, y in q) + 1e-3) for q in tris]
    items.sort(key=lambda it: it[2])
    for kind, q, _ in items:
        if kind == "b":
            box(d, q[0], q[1], hs, q[2], q[3], hb, pal["rib"])
        else:                                                    # mặt vát đứng + mặt trên
            (x1, y1), (x2, y2) = q[1], q[2]
            poly(d, [(x1, y1, hs), (x2, y2, hs), (x2, y2, hb), (x1, y1, hb)], shade(pal["rib"], 0.72))
            poly(d, [(x, y, hb) for x, y in q], shade(pal["rib"], 1.06))
    # mặt trên chung: phủ màu rồi chỉ vẽ đường viền ngoài (cạnh dùng chung giữa các khối là cạnh trong)
    top = shade(pal["rib"], 1.06)
    polys = [[(q[0], q[1]), (q[2], q[1]), (q[2], q[3]), (q[0], q[3])] for q in pieces] + tris
    for pg in polys:
        d.polygon([P(x, y, hb) for x, y in pg], fill=top)
    edges = {}
    for pg in polys:
        for i in range(len(pg)):
            e0, e1 = pg[i], pg[(i + 1) % len(pg)]
            k = tuple(sorted((tuple(round(v, 6) for v in e0), tuple(round(v, 6) for v in e1))))
            edges[k] = edges.get(k, 0) + 1
    for (a0, a1), n in edges.items():
        if n == 1:
            d.line([P(a0[0], a0[1], hb), P(a1[0], a1[1], hb)], fill=EDGE, width=max(1, int(0.55 * SS)))
    a, hc, H = 1.3, 0.45, 3.9            # tim trụ, nửa cạnh cổ, cao cổ
    for x, y in ((-a, -a), (a, -a), (-a, a), (a, a)):                              # sau trước, trái phải
        box(d, x - hc, y - hc, hb, x + hc, y + hc, H, pal["pier"])
        for bx, by in ((-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)):
            cx, cy = x + bx, y + by
            x0, y0 = P(cx, cy, H)
            x1, y1 = P(cx, cy, H + 0.45)
            d.line([(x0, y0), (x1, y1)], fill=pal["bolt"] + (255,), width=int(1.1 * SS))
    bb = im.getbbox()                                  # cắt sát hình rồi đặt giữa ô vuông có lề
    im = im.crop(bb)
    side = int(max(im.width, im.height) * (1.22 if pal.get("bg") else 1.04))
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    if pal.get("bg"):                                  # nền vuông bo góc
        ImageDraw.Draw(sq).rounded_rectangle([0, 0, side - 1, side - 1], radius=side // 6, fill=pal["bg"] + (255,))
    sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return sq.resize((size, size), Image.LANCZOS)


def main(out, pal=None):
    im = draw(PALETTES[pal or PAL])
    im.save(out, format="ICO", sizes=[(SIZE, SIZE)])
    im.save(os.path.splitext(out)[0] + ".png")


if __name__ == "__main__":
    main(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.ico"))
