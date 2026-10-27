"""Tờ 1: mặt cắt A-A, mặt bằng móng (TKBVTC: có thép bản, thép dầm), bảng thống kê thép hoặc tổng kê."""
from __future__ import annotations

import math

from . import model, tables
from .cad import Ctx, txtw
from .geom import Geo
from .view import (V, Callouts, arrow2, bolt_side, bolts_plan, cut_line, elev, marker, note_at, phi, sym, sym_r, tick45,
                   title, vee)

T_SOIL = "ĐẤT THỪA ĐẮP LẠI"
T_FILL = "ĐẤT ĐẮP ĐẦM CHẶT"
T_AXIS = "TIM MÓNG"
T_CUSHION = "ĐỆM CÁT - DÀY "
T_GEO = "VẢI ĐỊA KỸ THUẬT"
T_ROUTE = "HƯỚNG TUYẾN"
T_BISECT = "HƯỚNG PHÂN GIÁC"
T_LADDER = "THANG LEO"
TABLE_X = 268.0          # mép trái bảng thống kê thép (tờ 1)


def fx(x, n):
    return f"{abs(x):.{n}f}"


def layout(g: Geo):
    """Vị trí giấy của mặt cắt A-A và mặt bằng trên tờ 1."""
    p, k = g.p, g.k
    sl = model.SLOPE_DRAW
    g.pitB = g.Lh + p["MPIT"]                                   # nửa đáy hố (m)
    g.pitT = g.pitB + sl * model.pit_depth(p)                   # nửa miệng hố (m)
    xmax = TABLE_X - 6.0 if model.is_detail(p) else 262.0
    g.cx = min(max(100.2, 62.0 + k * g.pitT), xmax - 10.0 - k * g.pitT)
    g.ytop = 262.2
    g.ybase = g.ytop - k * g.H
    g.ygl = g.ybase + k * p["H1"]
    g.ylt = g.ybase - k * model.TL
    g.ylb = g.ylt - k * p["HC"]
    g.yd = g.ylb - 10.4
    g.planTop = g.yd - 22.0
    g.cy = g.planTop - k * (g.Bh + model.ML)
    g.xgl = g.cx - k * g.pitT
    g.dimX1 = g.xgl - 21.0
    g.dimX2 = g.xgl - 13.2


# ---------------------------------------------------------------------------
def outline_aa(v: V, g: Geo, u0=None):
    """Đường bao bê tông mặt cắt A-A (cắt tại y = 0, nhìn theo +Y). u0 = 0: chỉ vẽ nửa phải."""
    L, hs, hd, a, e, b, c = g.Lh, g.hs, g.hd, g.a, g.e, g.bb, g.c
    lo = -1e9 if u0 is None else u0

    def h(lay, z, x1, x2):
        x1, x2 = max(x1, lo), max(x2, lo)
        if x2 - x1 > 1e-6:
            v.ln(lay, x1, z, x2, z)

    def vl(lay, x, z1, z2):
        if x >= lo - 1e-9:
            v.ln(lay, x, z1, x, z2)
    h("MAIN", 0.0, -L, L)
    # đỉnh dầm theo X phía sau: dừng tại mặt cổ móng; trong phạm vi cổ chỉ còn đỉnh dầm theo Y bị cắt
    xs = [-L, -g.dx - b / 2, -g.dx + b / 2, g.dx - b / 2, g.dx + b / 2, L]
    for i in (0, 2, 4):
        h("MAIN", hd, xs[i], xs[i + 1])
    for s in (-1, 1):
        h("MAIN", hd, s * g.dx - a / 2, s * g.dx + a / 2)
    vl("MAIN", -L, 0.0, hd)
    vl("MAIN", L, 0.0, hd)
    # mặt trên bản (giữa các dầm theo Y bị cắt)
    xs = [-L, -g.dx - a / 2, -g.dx + a / 2, g.dx - a / 2, g.dx + a / 2, L]
    for i in (0, 2, 4):
        h("MAIN", hs, xs[i], xs[i + 1])
    for s in (-1, 1):
        for t in (-1, 1):
            vl("MAIN", s * g.dx + t * a / 2, hs, hd)
            if g.hasHaunch:
                vl("HINH THUC", s * g.dx + t * (a / 2 + e), hs, hd)
        # cổ móng phía sau
        for t in (-1, 1):
            vl("MAIN", s * g.dx + t * b / 2, hd, g.H)
        x1, x2 = s * g.dx - b / 2, s * g.dx + b / 2
        h("MAIN", g.H, x1, x2)
    if g.hasHole:
        for s in (-1, 1):
            vl("MAIN", s * c / 2, 0.0, hs)
    # bê tông lót: nhìn xuyên lỗ mở thấy lót phía sau -> nét liền; hatch chỉ ở phần bị cắt
    ml, tl = model.ML, model.TL
    x0 = max(-L - ml, lo)
    v.rect("HINH THUC", x0, -tl, L + ml, 0.0)
    hole = g.hasHole and g.c > 2 * ml
    pcs = [(-L - ml, -(c / 2 - ml)), (c / 2 - ml, L + ml)] if hole else [(-L - ml, L + ml)]
    if hole:
        for s in (-1, 1):
            vl("HINH THUC", s * (c / 2 - ml), -tl, 0.0)
    for x1, x2 in pcs:
        x1 = max(x1, lo)
        if x2 - x1 < 1e-6:
            continue
        v.hatch("HATCH", [(x1, -tl), (x2, -tl), (x2, 0.0), (x1, 0.0)], "AR-CONC", 0.375 * v.k / 10.0)


def ladder_zs(g: Geo):
    s = g.g("TL_S") / 1000.0
    return [g.H - g.cov - i * s for i in range(g.n_ladder())]


def ladder_aa(c: Ctx, v: V, g: Geo, xf, sg, label=T_LADDER):
    """Thang leo nhìn ngang: bậc cắm vào cổ và nhô ra khỏi mặt cổ xf (sg: hướng nhô ra).
    Chú thích: đường đứng qua đầu các bậc có dấu xẹt, leader ngang ở bậc trên cùng."""
    zs = ladder_zs(g)
    if not zs:
        return None
    from .geom import TL_OUT
    for z in zs:
        v.ln("COTTHEP", xf - sg * 0.05, z, xf + sg * TL_OUT, z)
    xt = xf + sg * 0.6 * TL_OUT
    if label:
        with c.item("ladder", "Ghi chú thang leo"):
            c.ln("CHU", v.x(xt), v.y(zs[-1]), v.x(xt), v.y(zs[0]), fixed1=True, fixed2=True)
            for z in zs:
                tick45(c, v.x(xt), v.y(z), fixed=True)
            w = txtw(label, 2.0)
            xe = v.x(xt) + sg * (w + 2.0)
            zl = zs[0]
            if abs(xe - v.x(0.0)) < 6.5 or (xe - v.x(0.0)) * (v.x(xt) - v.x(0.0)) < 0:
                zl = zs[-1]                     # tránh ký hiệu đối xứng ở đỉnh trục -> ghi ở bậc dưới cùng
            c.ln("CHU", v.x(xt), v.y(zl), xe, v.y(zl), fixed1=True)
            c.txj("CHU", v.x(xt) + sg * 1.0, v.y(zl) + 0.8, 2.0, label, 0 if sg > 0 else 2)
    return xt, zs


def draw_section(c: Ctx, g: Geo):
    p, k = g.p, g.k
    v = V(c, g.cx, g.ybase, g.den)
    outline_aa(v, g)
    cx = g.cx
    hp, ht = k * g.pitB, k * g.pitT
    # mặt đất, hố đào
    ygl = g.ygl
    if p["H1"] < g.hd - 1e-6:            # mặt dầm cao hơn mặt đất
        segs = [(cx - ht - 8.0, cx - k * g.Lh), (cx + k * g.Lh, cx + ht + 8.0)]
    else:
        segs, x0 = [], cx - ht - 8.0
        for s in (-1, 1):
            segs.append((x0, cx + k * (s * g.dx - g.bb / 2)))
            x0 = cx + k * (s * g.dx + g.bb / 2)
        segs.append((x0, cx + ht + 8.0))
    for x1, x2 in segs:
        c.ln("HINH THUC", x1, ygl, x2, ygl)
    c.ln("HINH THUC", cx - hp, g.ylb, cx - ht, ygl)
    c.ln("HINH THUC", cx + hp, g.ylb, cx + ht, ygl)
    c.ln("HINH THUC", cx - hp, g.ylb, cx + hp, g.ylb)
    if g.hasCushion:
        draw_cushion(c, g)
    # trục
    for s in (-1, 1):
        c.ln("TRUC", cx + s * k * g.dx, g.ytop + 4.3, cx + s * k * g.dx, g.ylb - 2.2)
    c.ln("TRUC", cx, g.ylb - 1.5, cx, g.ytop + 4.4)
    sym(c, cx, g.ytop - 0.5)
    ybt = g.ytop
    ph = k * g.bb / 2
    for s in (-1, 1):
        for t in (-1, 1):
            ybt = bolt_side(c, k, cx + s * k * g.dx + t * 0.47 * ph, g.ytop)
    xb = cx + k * g.dx + 0.47 * ph + 1.1
    yb = (g.ytop + ybt) / 2
    with c.item("bln", "Ghi chú bu lông"):
        c.ln("CHU", xb, yb, xb + 6.0, yb, fixed1=True)
        c.tx("CHU", xb + 7.0, yb - 0.8, 1.6, p["BLN"])
    # thang leo trên cổ móng trái (trụ phía sau mặt cắt), mặt quay vào tim
    ladder_aa(c, v, g, -g.dx + g.bb / 2, 1)
    # cao độ
    elev(c, g.dimX2 - 17.4, g.ybase, f"-{fx(p['H1'], 2)}m")
    elev(c, g.dimX2 - 17.4, ygl, "%%p0.00")
    elev(c, g.dimX2 - 5.4, g.ytop, f"+{fx(p['H2'], 2)}m")
    if g.hasCushion:
        elev(c, g.dimX2 - 17.4, g.ylb, f"-{fx(p['H1'] + model.TL + p['HC'], 2)}m")
    # đất đắp: ụ đất thừa giữa 2 cổ móng (khi mặt dầm không cao hơn mặt đất)
    if p["H1"] >= g.hd - 1e-6:
        pa = ygl + 3.1
        sx = cx - k * g.Lh
        xi = cx - k * (g.dx + g.bb / 2)
        xa = min(sx + 3.2, xi - 0.5)
        c.ln("HINH THUC", sx, ygl, xa, pa)
        c.ln("HINH THUC", xa, pa, xi, pa)
        c.ln("HINH THUC", cx - k * (g.dx - g.bb / 2), pa, cx + k * (g.dx - g.bb / 2), pa)
        c.ln("HINH THUC", 2 * cx - sx, ygl, 2 * cx - xa, pa)
        c.ln("HINH THUC", 2 * cx - xa, pa, 2 * cx - xi, pa)
        xl = xi - 2.8
        with c.item("soil", "Ghi chú đất đắp"):
            w = txtw(T_SOIL, 2.0)
            c.pl("CHU", False, [(xl, ygl + 1.4), (xl - 4.2, ygl + 5.6), (xl - 4.7 - w, ygl + 5.6)], fixed=(0,))
            c.tx("CHU", xl - 4.6 - w, ygl + 6.4, 2.0, T_SOIL)
    xf = cx + k * (g.Lh + 0.6 * (g.pitT - g.Lh))
    with c.item("fill", "Ghi chú đất đắp đầm chặt"):
        c.pl("CHU", False, [(xf, ygl - 2.0), (xf + 4.0, ygl + 4.5), (xf + 4.4 + txtw(T_FILL, 2.0), ygl + 4.5)],
             fixed=(0,))
        c.tx("CHU", xf + 4.2, ygl + 5.3, 2.0, T_FILL)
    title(c, cx, g.yd - 7.5, "MẶT CẮT A-A", f"TL:1/{g.den}")


def draw_cushion(c: Ctx, g: Geo):
    cx, k, hc, s = g.cx, g.k, g.p["HC"], model.SLOPE_DRAW
    hp = k * g.pitB
    yv = g.ylt
    xw = cx - hp - k * s * hc
    xf = cx - k * g.Lh + 0.5 * k
    lbl = f"{T_CUSHION}{int(1000 * hc + 0.5)}mm"
    yl = (g.ylt + g.ylb) / 2 - 1.0
    wl = txtw(lbl, 2.0) / 2 + 0.8
    with c.item("cushion", "Ghi chú đệm cát"):
        c.txc("CHU", cx, yl, 2.0, lbl)
        di = c.item_off()
    hole = [(cx - wl + di[0], yl - 1.6 + di[1]), (cx + wl + di[0], yl - 1.6 + di[1]),
            (cx + wl + di[0], yl + 1.6 + di[1]), (cx - wl + di[0], yl + 1.6 + di[1])]
    c.hatch("HATCH", [(cx - hp, g.ylb), (cx + hp, g.ylb), (2 * cx - xw, g.ylt), (xw, g.ylt)], "AR-SAND", 1.2,
            holes=[hole] if 2 * 1.6 < (g.ylt - g.ylb) else ())
    c.pl("VAI DIA", False, [(xf + 1.3, yv - 1.3), (xf, yv), (xw, yv), (cx - hp, g.ylb), (cx + hp, g.ylb),
                            (2 * cx - xw, yv), (2 * cx - xf, yv), (2 * cx - xf - 1.3, yv - 1.3)])
    xg = cx + 0.3 * hp
    with c.item("geo", "Ghi chú vải địa"):
        c.pl("CHU", False, [(xg, g.ylb), (xg - 3.5, g.ylb - 4.0), (xg - 3.5 - 25.0, g.ylb - 4.0)], fixed=(0,))
        c.tx("CHU", xg - 3.5 - 25.0, g.ylb - 3.2, 2.0, T_GEO)


def dim_section(c: Ctx, g: Geo):
    p, k, cx = g.p, g.k, g.cx
    w100 = txtw("100", 2.0)
    s = model.SLOPE_DRAW
    hc = p["HC"]
    L = g.Lh
    xa = g.xgl - 3.0
    # bên trái: H1, H2 (ngoài); bản, dầm, cổ (trong)
    c.dimV("DIM", (xa, g.ygl), (xa, g.ybase), g.dimX1)
    c.dimV("DIM", (xa, g.ygl), (xa, g.ytop), g.dimX1)
    # đường gióng chỉ kéo tới gần mép miệng hố (không chạy vào trong hình)
    c.dimV("DIM", (xa, g.ybase), (xa, g.ybase + k * g.hs), g.dimX2)
    c.dimV("DIM", (xa, g.ybase + k * g.hs), (xa, g.ybase + k * g.hd), g.dimX2)
    c.dimV("DIM", (xa, g.ybase + k * g.hd), (xa, g.ytop), g.dimX2)
    xr1 = cx - k * (g.pitB + (s * (hc + model.TL) if g.hasCushion else 0.0))
    xd = xr1 - 8.5
    xpb = cx - k * (g.pitB + (s * hc if g.hasCushion else 0.0))
    if g.hasCushion:
        yt = g.ybase + 1.0 + w100 / 2
        c.dimV("DIM", (cx - k * (L + model.ML), g.ybase), (xpb, g.ylt), xd, (xd - 2.0, yt))
        c.ln("DIM", xd, g.ybase, xd, g.ybase + 1.0 + w100)
        c.dimV("DIM", (cx - k * (g.pitB + s * hc), g.ylt), (cx - k * g.pitB, g.ylb), xd)
    else:
        c.dimV("DIM", (cx - k * (L + model.ML), g.ybase), (xpb, g.ylt), xd)
    # bên phải: cao dầm tổng
    xr = cx + k * L
    c.dimV("DIM", (xr, g.ybase), (xr, g.ybase + k * g.hd), xr + 7.0)
    # ngang dưới mặt cắt
    hl = k * (L + model.ML)
    yb = g.ylb          # đường gióng đặt từ mép dưới lớp đệm cát (không xuyên qua lớp cát)
    c.dimH("DIM", (cx - k * L, yb), (cx + k * L, yb), g.yd)
    c.dimH("DIM", (cx + k * L, yb), (cx + hl, yb), g.yd, (cx + hl - 0.5, g.yd - 4.5))
    c.dimH("DIM", (cx - k * L, yb), (cx - hl, yb), g.yd, (cx - hl + 0.5, g.yd - 4.5))
    c.dimH("DIM", (cx - hl, yb), (cx - k * g.pitB, yb), g.yd, (cx - k * g.pitB - 3.2, g.yd + 1.7))
    c.dimH("DIM", (cx + hl, yb), (cx + k * g.pitB, yb), g.yd, (cx + k * g.pitB + 3.2, g.yd + 1.7))
    if g.hasCushion:
        # đoạn vải địa gấp vào dưới móng 500: đường gióng đặt từ mép dưới lớp đệm cát
        for x1, x2 in ((cx - k * L, cx - k * L + 0.5 * k), (cx + k * L - 0.5 * k, cx + k * L)):
            c.dimH("DIM", (x1, g.ylb), (x2, g.ylb), g.ylb - 5.0)
    # trên: tim cổ móng, bề rộng cổ móng
    y1, y2 = g.ytop + 6.0, g.ytop + 12.9
    for s_ in (-1, 1):
        c.dimH("DIM", (cx + k * (s_ * g.dx - g.bb / 2), g.ytop), (cx + k * (s_ * g.dx + g.bb / 2), g.ytop), y1)
    c.dimH("DIM", (cx - k * L, g.ybase + k * g.hd), (cx - k * g.dx, g.ytop + 4.3), y2)
    c.dimH("DIM", (cx - k * g.dx, g.ytop + 4.3), (cx + k * g.dx, g.ytop + 4.3), y2)
    c.dimH("DIM", (cx + k * g.dx, g.ytop + 4.3), (cx + k * L, g.ybase + k * g.hd), y2)


# ---------------------------------------------------------------------------
def panels(g: Geo):
    """Các ô bản giữa các dầm: (x0, x1, y0, y1) - mép là mặt dầm hoặc mép móng."""
    a = g.a
    xs = [(-g.Lh, -g.dx - a / 2), (-g.dx + a / 2, g.dx - a / 2), (g.dx + a / 2, g.Lh)]
    ys = [(-g.Bh, -g.dy - a / 2), (-g.dy + a / 2, g.dy - a / 2), (g.dy + a / 2, g.Bh)]
    return [(x0, x1, y0, y1) for x0, x1 in xs for y0, y1 in ys]


def plan_outline(c: Ctx, g: Geo, v: V, bolts=True, lot=True):
    L, B, e = g.Lh, g.Bh, g.e
    ml = model.ML
    if lot:
        v.rect("HINH THUC", -L - ml, -B - ml, L + ml, B + ml)
    v.rect("MAIN", -L, -B, L, B)
    # mép dầm + vát nách (theo từng ô bản)
    for x0, x1, y0, y1 in panels(g):
        ex = lambda x: abs(abs(x) - L) < 1e-6
        ey = lambda y: abs(abs(y) - B) < 1e-6
        cs = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pts = []
        for i, (x, y) in enumerate(cs):
            if not ex(x) and not ey(y) and g.hasHaunch:      # góc giáp chỗ giao dầm -> vát
                px, py = cs[i - 1]
                nx, ny = cs[(i + 1) % 4]
                d1 = (math.copysign(e, px - x) if px != x else 0.0, math.copysign(e, py - y) if py != y else 0.0)
                d2 = (math.copysign(e, nx - x) if nx != x else 0.0, math.copysign(e, ny - y) if ny != y else 0.0)
                pts += [(x + d1[0], y + d1[1]), (x + d2[0], y + d2[1])]
            else:
                pts.append((x, y))
        n = len(pts)
        for i in range(n):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
            on_edge = (ex(xa) and ex(xb) and abs(xa - xb) < 1e-9) or (ey(ya) and ey(yb) and abs(ya - yb) < 1e-9)
            if not on_edge:
                v.ln("MAIN", xa, ya, xb, yb)
    # cổ móng
    ph = v.k * g.bb / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * g.dx, sy * g.dy
            v.rect("MAIN", px - g.bb / 2, py - g.bb / 2, px + g.bb / 2, py + g.bb / 2)
            if bolts:
                bolts_plan(c, v.x(px), v.y(py), ph)
    # lỗ mở
    if g.hasHole:
        h = g.c / 2
        v.rect("MAIN", -h, -h, h, h)
        if lot and h > ml:
            v.rect("HINH THUC", -h + ml, -h + ml, h - ml, h - ml)
    # trục
    for s in (-1, 1):
        v.ln("TRUC", s * g.dx, -B - 0.3, s * g.dx, B + 0.3)
        v.ln("TRUC", -L - 0.3, s * g.dy, L + 0.3, s * g.dy)
    v.ln("TRUC", -L - 0.3, 0.0, L + 0.3, 0.0)
    v.ln("TRUC", 0.0, -B - 0.3, 0.0, B + 0.3)


def draw_route(c: Ctx, g: Geo, cx, cy, lh, lx, k=None):
    """Hướng tuyến đi qua tim móng (quy ước app cũ): đỡ - 2 chiều theo Y; néo góc - 2 tia lệch 10°,
    phân giác hướng sang trái; néo dừng - 1 chiều."""
    ht = int(g.p["HT"])
    wr = txtw(T_ROUTE, 2.0)
    a = max(4.6 + wr / 2, min(0.5 * lh, lh - 2.4 - wr / 2))
    if k:                                  # ưu tiên khoảng trống giữa mép dầm và mép bản
        z0 = k * (g.dy + g.a / 2) + 1.0
        if lh - 1.0 - z0 >= wr + 1.0:
            a = 0.5 * (z0 + lh - 1.0)
    if ht == 1:
        dlt = math.radians(10.0)
        sn, cs = math.sin(dlt), math.cos(dlt)
        vee(c, cx, cy, cx - lh * sn, cy + lh * cs)
        vee(c, cx, cy, cx - lh * sn, cy - lh * cs)
        c.txr("CHU", cx - a * sn - 2.4 * cs, cy + a * cs - 2.4 * sn, 2.0, T_ROUTE, 90.0 + 10.0)
        vee(c, cx, cy, cx - lx, cy)
        c.tx("CHU", cx - lx + 1.0, cy + 1.2, 2.0, T_BISECT)
    elif ht == 2:
        vee(c, cx, cy, cx, cy - lh)
        c.txr("CHU", cx - 2.4, cy - a, 2.0, T_ROUTE, 90.0)
    else:
        vee(c, cx, cy, cx, cy - lh)
        vee(c, cx, cy, cx, cy + lh)
        c.txr("CHU", cx - 2.4, cy + a, 2.0, T_ROUTE, 90.0)


def dim_plan(c: Ctx, g: Geo, v: V):
    L, B, a, ml = g.Lh, g.Bh, g.a, model.ML
    x0 = v.x(-L - ml)
    # trái: chuỗi mặt dầm (trong), tim dầm (giữa), tổng (ngoài)
    ys = [-B - ml, -B, -g.dy - a / 2, -g.dy + a / 2, g.dy - a / 2, g.dy + a / 2, B, B + ml]
    w100 = txtw("100", 2.0)
    for i in range(len(ys) - 1):
        tp = None
        if i in (0, len(ys) - 2):
            yy = v.y(ys[i]) - 1.0 - w100 / 2 if i == 0 else v.y(ys[i + 1]) + 1.0 + w100 / 2
            tp = (x0 - 10.0 - 2.0, yy)
        v.dimV((-L - ml, ys[i]), (-L - ml, ys[i + 1]), x0 - 10.0, tp)
    # điểm đo đặt ở mép lót -> đường gióng có khe hở với nét bê tông lót
    for y1, y2 in ((-B, -g.dy), (-g.dy, g.dy), (g.dy, B)):
        v.dimV((-L - ml, y1), (-L - ml, y2), x0 - 17.0)
    v.dimV((-L - ml, -B), (-L - ml, B), x0 - 24.0)
    # dưới
    y0 = v.y(-B - ml)
    xs = [-L - ml, -L, -g.dx - a / 2, -g.dx + a / 2, g.dx - a / 2, g.dx + a / 2, L, L + ml]
    for i in range(len(xs) - 1):
        tp = None
        if i in (0, len(xs) - 2):
            xx = v.x(xs[i]) - 1.0 - w100 / 2 if i == 0 else v.x(xs[i + 1]) + 1.0 + w100 / 2
            tp = (xx, y0 - 5.0 + 2.0)
        v.dimH((xs[i], -B - ml), (xs[i + 1], -B - ml), y0 - 5.0, tp)
    for x1, x2 in ((-L, -g.dx), (-g.dx, g.dx), (g.dx, L)):
        v.dimH((x1, -B - ml), (x2, -B - ml), y0 - 12.0)
    v.dimH((-L, -B - ml), (L, -B - ml), y0 - 19.0)
    # cổ móng, vát nách, lỗ mở (góc trên trái)
    px, py = -g.dx, g.dy
    bb = g.bb
    v.dimH((px - bb / 2, py + bb / 2), (px + bb / 2, py + bb / 2), v.y(py + bb / 2) + 3.5)
    v.dimV((px - bb / 2, py - bb / 2), (px - bb / 2, py + bb / 2), v.x(px - bb / 2) - 3.5)
    if g.hasHaunch:
        qx, qy = -g.dx, -g.dy
        xa = qx + a / 2
        v.dimH((xa, qy + a / 2), (xa + g.e, qy + a / 2), v.y(qy + a / 2 + g.e) + 2.5)
        v.dimV((xa, qy + a / 2), (xa, qy + a / 2 + g.e), v.x(xa + g.e) + 2.5)        # cạnh vát phương còn lại
    if g.hasHole:
        h = g.c / 2
        ml_ = model.ML if h > model.ML else 0.0
        xs = [-h, -h + ml_, h - ml_, h] if ml_ else [-h, h]
        for i in range(len(xs) - 1):          # lỗ mở + lót tràn vào lỗ 100 mỗi bên
            v.dimH((xs[i], -h), (xs[i + 1], -h), v.y(-h) - 3.0)
            v.dimV((-h, xs[i]), (-h, xs[i + 1]), v.x(-h) - 3.0)


def tim_mong(c: Ctx, cx, cy, r):
    """Ký hiệu tim móng: vòng tròn, tô đen 2 góc phần tư đối đỉnh."""
    c.ci("CHU", cx, cy, r)
    for a0 in (0.0, 180.0):
        pts = [(cx, cy)] + [(cx + r * math.cos(math.radians(a0 + t)), cy + r * math.sin(math.radians(a0 + t)))
                            for t in range(0, 91, 10)]
        c.solid("CHU", pts)


def draw_plan(c: Ctx, g: Geo, detail: bool):
    v = V(c, g.cx, g.cy, g.den)
    k = g.k
    plan_outline(c, g, v)
    cx, cy = g.cx, g.cy
    tim_mong(c, cx, cy, 1.2)
    with c.item("axis", "Ghi chú tim móng"):
        xh = cx - k * g.c / 2 - 2.0 if g.hasHole else cx
        sg = -1.0 if int(g.p["HT"]) == 1 else 1.0         # néo góc: chữ phân giác ở trên trục -> ghi tim móng ở dưới
        c.pl("CHU", False, [(cx, cy), (xh - 3.0, cy + sg * 4.7), (xh - 17.4, cy + sg * 4.7)], fixed=(0,))
        c.tx("CHU", xh - 17.7, cy + sg * 4.7 + 0.9, 2.0, T_AXIS)
    draw_route(c, g, cx, cy, k * g.Bh - 1.0, k * g.Lh - 1.0, k)
    sym(c, cx, v.y(g.Bh + model.ML) + 3.0)
    sym_r(c, v.x(-g.Lh - model.ML) - 3.0, cy, 90.0)
    # ký hiệu mặt cắt A-A
    xl, xr = v.x(-g.Lh - model.ML) - 36.0, v.x(g.Lh + model.ML) + 22.0
    if detail:
        xr = v.x(g.Lh + model.ML) + 5.0 + 7.76
    marker(c, xl, cy, 1.0, "A")
    marker(c, xr, cy, -1.0, "A")
    if detail:
        plan_marks(c, g, v)
        plan_bars(c, g, v)
    dim_plan(c, g, v)
    title(c, cx, v.y(-g.Bh) - 28.5, "MẶT BẰNG MÓNG", f"TL:1/{g.den}")


def plan_marks(c: Ctx, g: Geo, v: V):
    """Vết cắt 1-1 (ngang qua dầm theo Y), 2-2 (ngang qua dầm theo X), 3-3 (song song mặt vát nách)."""
    a, W = g.a, 0.3
    y1 = -(g.dy + a / 2 + g.e + g.D2 / 2)
    cut_line(c, v.P(-g.dx - a / 2 - W, y1), v.P(-g.dx + a / 2 + W, y1), "1", ext=0.5)
    x2 = -(g.dx + a / 2 + g.e + g.D1 / 2)
    cut_line(c, v.P(x2, -g.dy + a / 2 + W), v.P(x2, -g.dy - a / 2 - W), "2", ext=0.5)
    if g.hasHaunch:
        qx, qy = -g.dx, -g.dy
        ext = 0.25
        p1 = v.P(qx + 1.5 * a + g.e - g.cov + ext, qy - a / 2 - ext)
        p2 = v.P(qx - a / 2 - ext, qy + 1.5 * a + g.e - g.cov + ext)
        cut_line(c, p1, p2, "3", ext=1.0)


def plan_bars(c: Ctx, g: Geo, v: V):
    """Thép đại diện trên mặt bằng (nửa phải): thép bản các vùng, thép xiên góc lỗ, thép chủ dầm.
    Leader dùng các đoạn vuông góc; đường rải thép có mũi tên 2 đầu."""
    p = g.p
    co = Callouts(c, g)
    L, B, a, cov = g.Lh, g.Bh, g.a, g.cov
    d = p["RS_D"]
    xr = v.x(L + model.ML) + 3.0
    cx_ = v.x(0.0)

    def mid(lst):
        return lst[len(lst) // 2] if lst else None

    # --- thanh theo X (thép 3, 4) ở nửa trên: đường rải đứng gần mép phải; leader chạm đường rải
    zones = []
    for z0, z1, kd in g.zones(B, g.dy):
        if z0 >= -1e-9:
            zones.append((3, [y for y in g.ys3 if z0 < y < z1], kd))
    if g.hasHole:
        zones.append((4, [y for y in g.ys4 if y >= -1e-9] or g.ys4, "in"))
    xm = L - 0.12 * (L - g.dx - a / 2)
    used = [v.y(g.dy + a / 2) + 7.0]
    for pos, ys, kd in sorted(zones, key=lambda z: -max(z[1]) if z[1] else 0):
        if not ys:
            continue
        y = ys[len(ys) // 3] if kd == "in" and pos == 3 else mid(ys)
        x0 = 0.0 if pos == 3 else g.c / 2 + cov
        v.ln("COTTHEP", x0, y, L - cov, y)
        yy = ys if pos == 3 else g.ys4
        arrow2(c, v.x(xm), v.y(min(yy)), v.x(xm), v.y(max(yy)))
        c.ci("CHU", v.x(xm), v.y(y), 0.5)
        s = p["RS_S2"] if kd == "out" else p["RS_S1"]
        lo_, hi_ = v.y(min(yy)), v.y(max(yy))
        by = 0.5 * (lo_ + hi_) + 2.5 if pos == 4 else 0.5 * (lo_ + hi_) + (0.2 * (hi_ - lo_) if kd == "in" else 0.0)
        for u in used:
            if abs(by - u) < 8.0:
                by = max(lo_ + 0.5, min(hi_ - 0.5, u - 8.0 if by < u else u + 8.0))
        used.append(by)
        if abs(by - v.y(y)) < 3.0:           # điểm chạm cách xa chấm thanh đại diện
            by = v.y(y) + 3.0 if v.y(y) + 3.0 <= hi_ - 0.3 else v.y(y) - 3.0
        yt = by
        if pos == 4 and by > v.y(0.0) - 10.0:     # chữ tag đè ký hiệu mặt cắt A (trên trục ngang) -> hạ xuống dưới
            yt = v.y(0.0) - 10.0
        co([(v.x(xm), by)], xr, yt, 1, pos, phi(d, s), f"SL:{2 * len(yy)}%%C{int(d)} - 2 LỚP", tick=False,
           mode=yt == by)                     # tag bị hạ: leader xiên, không chạy trùng đường rải
    # --- thanh theo Y (thép 1, 2) ở nửa dưới: đường rải ngang gần mép dưới; leader chạm đường rải
    zones = []
    for z0, z1, kd in g.zones(L, g.dx):
        if z0 >= -1e-9:
            zones.append((1, [x for x in g.xs1 if z0 < x < z1], kd))
    if g.hasHole:
        zones.append((2, [x for x in g.xs2 if x >= -1e-9] or g.xs2, "in"))
    ybar = -B + 0.12 * g.D2
    yq = v.y(-g.dy) + 4.0
    ylo = v.y(ybar) + 3.0
    for pos, xs, kd in sorted(zones, key=lambda z: min(z[1]) if z[1] else 0):
        if not xs:
            continue
        x = mid(xs)
        y1 = 0.0 if pos == 1 else -g.c / 2 - cov
        v.ln("COTTHEP", x, -B + cov, x, y1)
        xx = xs if pos == 1 else g.xs2
        arrow2(c, v.x(min(xx)), v.y(ybar), v.x(max(xx)), v.y(ybar))
        c.ci("CHU", v.x(x), v.y(ybar), 0.5)
        s = p["RS_S2"] if kd == "out" else p["RS_S1"]
        xt = x + 3.0 / v.k if x + 3.0 / v.k <= max(xx) else x - 3.0 / v.k   # cách chấm thanh đại diện 3 mm
        yq -= 9.0
        by = max(ylo, yq)
        co([v.P(xt, ybar)], xr, by, 1, pos, phi(d, s), f"SL:{2 * len(xx)}%%C{int(d)} - 2 LỚP", tick=False,
           mode=True)
    # --- thép xiên góc lỗ (5) ở góc trên phải của lỗ; tag đặt ở khoảng trống phía trên lỗ,
    #     leader 1 đoạn ngang + 1 đoạn xiên
    if g.hasHole and g.n5:
        m = max(1, g.n5 // 8)
        cc = g.c / 2
        hl = g.l5 / 2
        s5 = p["RS_S1"] / 2000.0
        r2 = 1 / math.sqrt(2)
        pts = []
        for j in range(m):
            t = cov * math.sqrt(2) + 0.05 + j * s5
            ox, oy = cc + t * r2, cc + t * r2
            v.ln("COTTHEP", ox + r2 * hl, oy - r2 * hl, ox - r2 * hl, oy + r2 * hl)
            pts.append(v.P(ox - r2 * 0.45 * hl, oy + r2 * 0.45 * hl))
        q = pts[-1]
        yb = min(v.y(g.dy - a / 2 - g.e) - 4.0, q[1] + 6.0)
        co([q], max(q[0] - 2.0, cx_ + 3.5), yb, -1, 5, f"{g.n5 // 4}%%C{int(d)}", "02 LỚP")
    # --- thép chủ dầm: trên mặt bằng chỉ thấy các thanh lớp ngoài cùng, vẽ từ trục đối xứng tới đầu dầm
    full_y, cut_y = g.rib_len(True)
    full_x, cut_x = g.rib_len(False)
    row = g.rows_t[0][1]
    dm = int(p["RD_D"])
    for u, f in row:
        v.ln("COTTHEP", g.dx + u, 0.0, g.dx + u, (full_y if f else cut_y) / 2)
        v.ln("COTTHEP", 0.0, g.dy + u, (full_x if f else cut_x) / 2, g.dy + u)
    uf = [u for u, f in row if f]
    ex = v.x(g.dx + a / 2) + 0.8
    yt = 0.5 * (cut_y / 2 + full_y / 2)
    co([v.P(g.dx + u, yt) for u in uf], ex, v.y(yt), 1, 10, f"{g.n_full}%%C{dm}", mode=True)
    yc = 0.5 * (g.dy + a / 2 + g.e + cut_y / 2)
    if g.n_cut:
        co([v.P(g.dx + u, yc) for u, _ in row], ex, v.y(yc), 1, 11, f"{g.n_cut}%%C{dm}", mode=True)
    # kích thước đoạn cắt thép dầm
    # kích thước đoạn cắt tính từ mép móng
    v.dimV((g.dx - a / 2, cut_y / 2), (g.dx - a / 2, B), v.x(g.dx - a / 2) - 3.0)
    v.dimH((cut_x / 2, g.dy + a / 2), (L, g.dy + a / 2), v.y(g.dy + a / 2) + 2.5)
    xt = full_x / 2 - 0.25            # gần đầu thanh, tránh chữ kích thước đoạn cắt
    co([v.P(xt, g.dy + u) for u in uf], xr, v.y(g.dy + a / 2) + 7.0, 1, 13, f"{g.n_full}%%C{dm}", tick=True,
       mode=True)
    if g.n_cut:
        xc = 0.5 * (g.dx + a / 2 + g.e + cut_x / 2)
        co([v.P(xc, g.dy + u) for u, _ in row], v.x(xc), v.y(g.dy - a / 2) - 4.0, 1, 14, f"{g.n_cut}%%C{dm}",
           mode=True)


# ---------------------------------------------------------------------------
def draw(c: Ctx, g: Geo):
    if not getattr(g, "kl", None):
        g.calc_kl()
    layout(g)
    detail = model.is_detail(g.p)
    with c.group("section", "Mặt cắt A-A"):
        draw_section(c, g)
        dim_section(c, g)
    with c.group("plan", "Mặt bằng móng"):
        draw_plan(c, g, detail)
    note = "- XEM GHI CHÚ CHUNG TẠI BẢN VẼ SỐ: " + str(g.p.get("CODE", ""))
    if detail:
        tables.steel_table(c, g, TABLE_X, 280.0, 70.0)
    else:
        tables.summary(c, g, 395.0, 267.0)
        note_at(c, 268.0, 90.0, [note])
