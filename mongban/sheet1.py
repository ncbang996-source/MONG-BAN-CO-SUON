"""Tờ 1: mặt cắt A-A, mặt bằng móng (TKBVTC: có thép bản, thép dầm), bảng thống kê thép hoặc tổng kê."""
from __future__ import annotations

import math

from . import model, tables
from .cad import Ctx, txtw
from .geom import Geo
from .view import (V, Callouts, bolt_side, bolts_plan, cut_line, elev, marker, note_at, phi, sym, tick45,
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
    lo = -L if u0 is None else u0

    def h(lay, z, x1, x2):
        x1, x2 = max(x1, lo), max(x2, lo)
        if x2 - x1 > 1e-6:
            v.ln(lay, x1, z, x2, z)

    def vl(lay, x, z1, z2):
        if x >= lo - 1e-9:
            v.ln(lay, x, z1, x, z2)
    h("MAIN", 0.0, -L, L)
    h("MAIN", hd, -L, L)
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
    # bê tông lót
    ml, tl = model.ML, model.TL
    pcs = [(-L - ml, -(c / 2 - ml)), (c / 2 - ml, L + ml)] if g.hasHole and c > 2 * ml else [(-L - ml, L + ml)]
    for x1, x2 in pcs:
        x1 = max(x1, lo)
        if x2 - x1 < 1e-6:
            continue
        v.rect("HINH THUC", x1, -tl, x2, 0.0)
        v.hatch("HATCH", [(x1, -tl), (x2, -tl), (x2, 0.0), (x1, 0.0)], "AR-CONC", 0.375 * v.k / 10.0)


def ladder_aa(v: V, g: Geo, piers, label=True):
    """Thang leo nhìn ngang trên các cổ móng (danh sách hoành độ mặt cổ, hướng nhô ra)."""
    n = g.n_ladder()
    if not n:
        return None
    s = g.g("TL_S") / 1000.0
    zs = [g.H - g.cov - i * s for i in range(n)]
    out = None
    for xf, sg in piers:
        xo = xf + sg * 0.15
        v.ln("CHU", xo, zs[-1], xo, zs[0])
        for z in zs:
            v.ln("CHU", xf, z, xo, z)
        out = (v.x(xo), v.y(0.5 * (zs[0] + zs[-1])), sg)
    return out


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
    lad = ladder_aa(v, g, [(-g.dx + g.bb / 2, 1)])
    if lad:
        with c.item("ladder", "Ghi chú thang leo"):
            x0, y0, _ = lad
            c.ln("CHU", x0, y0, x0 + 2.5, y0 - 2.5, fixed1=True)
            c.ln("CHU", x0 + 2.5, y0 - 2.5, x0 + 3.0 + txtw(T_LADDER, 2.0), y0 - 2.5)
            c.tx("CHU", x0 + 3.0, y0 - 1.8, 2.0, T_LADDER)
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
            c.pl("CHU", False, [(xl, ygl + 1.4), (xl - 5.6, ygl + 5.6), (xl - 32.1, ygl + 5.6)], fixed=(0,))
            di = c.item_off()
            c.arrow("CHU", xl - 5.6 + di[0], ygl + 5.6 + di[1], xl, ygl + 1.4, 1.6, 0.4, fixed=True)
            c.tx("CHU", xl - 32.2, ygl + 6.4, 2.0, T_SOIL)
    xf = cx + k * (g.Lh + 0.6 * (g.pitT - g.Lh))
    yf = g.ybase + 0.55 * (ygl - g.ybase)
    with c.item("fill", "Ghi chú đất đắp đầm chặt"):
        c.pl("CHU", False, [(xf, yf), (xf + 4.0, ygl + 4.5), (xf + 4.0 + txtw(T_FILL, 2.0) + 1.0, ygl + 4.5)],
             fixed=(0,))
        c.tx("CHU", xf + 4.5, ygl + 5.3, 2.0, T_FILL)
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
    xl = cx - k * L
    c.dimV("DIM", (xl, g.ybase), (xl, g.ybase + k * g.hs), g.dimX2)
    c.dimV("DIM", (xl, g.ybase + k * g.hs), (xl, g.ybase + k * g.hd), g.dimX2)
    c.dimV("DIM", (xl, g.ybase + k * g.hd), (cx - k * (g.dx + g.bb / 2), g.ytop), g.dimX2)
    xr1 = cx - k * (g.pitB + (s * (hc + model.TL) if g.hasCushion else 0.0))
    xd = xr1 - 4.5
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
    c.dimH("DIM", (cx - k * L, g.ybase + 1.2), (cx + k * L, g.ybase + 1.2), g.yd)
    c.dimH("DIM", (cx + k * L, g.ybase - 4.2), (cx + hl, g.ylt), g.yd, (cx + hl - 0.5, g.yd - 4.5))
    c.dimH("DIM", (cx - k * L, g.ybase), (cx - hl, g.ybase), g.yd, (cx - hl + 0.5, g.yd - 4.5))
    c.dimH("DIM", (cx - hl, g.ybase), (cx - k * g.pitB, g.ylb), g.yd, (cx - k * g.pitB - 3.2, g.yd + 1.7))
    c.dimH("DIM", (cx + hl, g.ybase), (cx + k * g.pitB, g.ylb), g.yd, (cx + k * g.pitB + 3.2, g.yd + 1.7))
    if g.hasCushion:
        c.dimH("DIM", (cx - k * L, g.ylt), (cx - k * L + 0.5 * k, g.ylt), g.ylb - 5.0)
        c.dimH("DIM", (cx + k * L - 0.5 * k, g.ylt), (cx + k * L, g.ylt), g.ylb - 5.0)
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


def draw_route(c: Ctx, g: Geo, cx, cy, lh, lx):
    ht = int(g.p["HT"])
    wr = txtw(T_ROUTE, 2.0)
    if ht == 1:
        dlt = math.radians(10.0)
        sn, cs = math.sin(dlt), math.cos(dlt)
        vee(c, cx, cy, cx + lh * sn, cy + lh * cs)
        vee(c, cx, cy, cx + lh * sn, cy - lh * cs)
        a = max(4.6 + wr / 2, min(0.5 * lh, lh - 2.4 - wr / 2))
        c.txr("CHU", cx + a * sn - 2.4 * cs, cy + a * cs + 2.4 * sn, 2.0, T_ROUTE, 90.0 - 10.0)
        vee(c, cx, cy, cx - lx, cy)
        c.tx("CHU", cx - lx + 1.0, cy + 1.2, 2.0, T_BISECT)
    elif ht == 2:
        vee(c, cx, cy, cx, cy - lh)
        c.txr("CHU", cx - 2.4, cy - 0.5 * lh, 2.0, T_ROUTE, 90.0)
    else:
        vee(c, cx, cy, cx, cy - lh)
        vee(c, cx, cy, cx, cy + lh)
        c.txr("CHU", cx - 2.4, cy + max(1.5 + wr / 2, min(0.5 * lh, lh - 2.4 - wr / 2)), 2.0, T_ROUTE, 90.0)


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
            tp = (x0 - 5.0 - 2.0, yy)
        v.dimV((-L, ys[i]), (-L, ys[i + 1]), x0 - 5.0, tp)
    for y1, y2 in ((-B, -g.dy), (-g.dy, g.dy), (g.dy, B)):
        v.dimV((-L, y1), (-g.dx, y2), x0 - 12.0)
    v.dimV((-L, -B), (-L, B), x0 - 19.0)
    # dưới
    y0 = v.y(-B - ml)
    xs = [-L - ml, -L, -g.dx - a / 2, -g.dx + a / 2, g.dx - a / 2, g.dx + a / 2, L, L + ml]
    for i in range(len(xs) - 1):
        tp = None
        if i in (0, len(xs) - 2):
            xx = v.x(xs[i]) - 1.0 - w100 / 2 if i == 0 else v.x(xs[i + 1]) + 1.0 + w100 / 2
            tp = (xx, y0 - 5.0 + 2.0)
        v.dimH((xs[i], -B), (xs[i + 1], -B), y0 - 5.0, tp)
    for x1, x2 in ((-L, -g.dx), (-g.dx, g.dx), (g.dx, L)):
        v.dimH((x1, -B), (x2, -g.dy), y0 - 12.0)
    v.dimH((-L, -B), (L, -B), y0 - 19.0)
    # cổ móng, vát nách, lỗ mở (góc trên trái)
    px, py = -g.dx, g.dy
    bb = g.bb
    v.dimH((px - bb / 2, py + bb / 2), (px + bb / 2, py + bb / 2), v.y(py + bb / 2) + 3.5)
    v.dimV((px - bb / 2, py - bb / 2), (px - bb / 2, py + bb / 2), v.x(px - bb / 2) - 3.5)
    if g.hasHaunch:
        qx, qy = -g.dx, -g.dy
        xa = qx + a / 2
        v.dimH((xa, qy + a / 2), (xa + g.e, qy + a / 2), v.y(qy + a / 2 + g.e) + 2.5)
    if g.hasHole:
        h = g.c / 2
        v.dimH((-h, -h), (h, -h), v.y(-h) - 3.0)
        v.dimV((-h, -h), (-h, h), v.x(-h) - 3.0)


def draw_plan(c: Ctx, g: Geo, detail: bool):
    v = V(c, g.cx, g.cy, g.den)
    k = g.k
    plan_outline(c, g, v)
    cx, cy = g.cx, g.cy
    c.ci("CHU", cx, cy, 1.2)
    with c.item("axis", "Ghi chú tim móng"):
        xh = cx - k * g.c / 2 - 2.0 if g.hasHole else cx
        c.pl("CHU", False, [(cx, cy), (xh - 3.0, cy - 4.7), (xh - 17.4, cy - 4.7)], fixed=(0,))
        c.tx("CHU", xh - 17.7, cy - 3.8, 2.0, T_AXIS)
    draw_route(c, g, cx - k * 0.35 * g.dx, cy, k * g.Bh - 1.0, k * (g.dx - g.a / 2) - 1.0)
    # ký hiệu mặt cắt A-A
    xl, xr = v.x(-g.Lh - model.ML) - 31.0, v.x(g.Lh + model.ML) + 22.0
    if detail:
        xr = v.x(g.Lh + model.ML) + 4.0
    marker(c, xl, cy, 1.0, "A")
    marker(c, xr, cy, -1.0, "A")
    if detail:
        plan_marks(c, g, v)
        plan_bars(c, g, v)
    dim_plan(c, g, v)
    title(c, cx, v.y(-g.Bh) - 28.5, "MẶT BẰNG MÓNG", f"TL:1/{g.den}")


def plan_marks(c: Ctx, g: Geo, v: V):
    """Vết cắt 1-1 (ngang qua dầm theo Y), 2-2 (ngang qua dầm theo X), 3-3 (song song mặt vát nách)."""
    a, W = g.a, 0.8
    y1 = -(g.dy + a / 2 + g.e + g.D2 / 2)
    cut_line(c, v.P(-g.dx - a / 2 - W, y1), v.P(-g.dx + a / 2 + W, y1), "1")
    x2 = -(g.dx + a / 2 + g.e + g.D1 / 2)
    cut_line(c, v.P(x2, -g.dy + a / 2 + W), v.P(x2, -g.dy - a / 2 - W), "2")
    if g.hasHaunch:
        qx, qy = -g.dx, -g.dy
        ext = 0.25
        p1 = v.P(qx + 1.5 * a + g.e - g.cov + ext, qy - a / 2 - ext)
        p2 = v.P(qx - a / 2 - ext, qy + 1.5 * a + g.e - g.cov + ext)
        cut_line(c, p1, p2, "3", ext=1.0)


def plan_bars(c: Ctx, g: Geo, v: V):
    """Thép đại diện trên mặt bằng (nửa phải): thép bản các vùng, thép xiên góc lỗ, thép chủ dầm."""
    p = g.p
    co = Callouts(c, g)
    L, B, a, cov = g.Lh, g.Bh, g.a, g.cov
    d = p["RS_D"]
    xr = v.x(L + model.ML) + 3.0
    used = [v.y(0.0)]

    def mid(lst):
        return lst[len(lst) // 2] if lst else None

    def tag_y(y0):
        y = y0
        for u in sorted(used):
            if abs(u - y) < 8.0:
                y = u + 8.0
        used.append(y)
        return y

    used += [v.y(g.dy) + 4.5, v.y(g.dy) - 4.5]
    # --- thanh theo X (thép 3, 4) ở nửa trên, chú thích bên phải
    zones = []
    for z0, z1, kd in g.zones(B, g.dy):
        if z0 >= -1e-9:
            ys = [y for y in g.ys3 if z0 < y < z1]
            zones.append((3, ys, kd))
    if g.hasHole:
        zones.append((4, [y for y in g.ys4 if y >= -1e-9] or g.ys4, "in"))
    for pos, ys, kd in sorted(zones, key=lambda z: -max(z[1]) if z[1] else 0):
        if not ys:
            continue
        y = mid(ys)
        x0 = 0.0 if pos == 3 else g.c / 2 + cov
        v.ln("COTTHEP", x0, y, L - cov, y)
        xm = L - 0.12 * (L - g.dx - a / 2)
        yy = ys if pos == 3 else (g.ys4 if g.ys4 else ys)
        v.ln("CHU", xm, min(yy), xm, max(yy))
        for q in (min(yy), max(yy)):
            tick45(c, v.x(xm), v.y(q))
        c.ci("CHU", v.x(xm), v.y(y), 0.5)
        s = p["RS_S2"] if kd == "out" else p["RS_S1"]
        n = 2 * len(yy) if pos == 3 else 4 * len(yy) // 2
        co([v.P(xm, y)], xr, tag_y(v.y(y)), 1, pos, phi(d, s), f"SL:{n}%%C{int(d)} - 2 LỚP", tick=False)
    # --- thanh theo Y (thép 1, 2) ở nửa dưới, chú thích bên phải phía dưới
    zones = []
    for z0, z1, kd in g.zones(L, g.dx):
        if z0 >= -1e-9:
            zones.append((1, [x for x in g.xs1 if z0 < x < z1], kd))
    if g.hasHole:
        zones.append((2, [x for x in g.xs2 if x >= -1e-9] or g.xs2, "in"))
    ybar = -B + 0.12 * g.D2
    yq = [v.y(-g.dy) + 4.0]
    for pos, xs, kd in sorted(zones, key=lambda z: min(z[1]) if z[1] else 0):
        if not xs:
            continue
        x = mid(xs)
        y1 = 0.0 if pos == 1 else -g.c / 2 - cov
        v.ln("COTTHEP", x, -B + cov, x, y1)
        xx = xs if pos == 1 else g.xs2
        v.ln("CHU", min(xx), ybar, max(xx), ybar)
        for q in (min(xx), max(xx)):
            tick45(c, v.x(q), v.y(ybar))
        c.ci("CHU", v.x(x), v.y(ybar), 0.5)
        s = p["RS_S2"] if kd == "out" else p["RS_S1"]
        n = 2 * len(xx)
        yq[0] -= 9.0
        co([v.P(x, ybar)], xr, yq[0], 1, pos, phi(d, s),
           f"SL:{n}%%C{int(d)} - 2 LỚP", tick=False)
    # --- thép xiên góc lỗ (5) ở góc trên phải của lỗ
    if g.hasHole and g.n5:
        m = max(1, g.n5 // 8)
        cc = g.c / 2
        hl = g.l5 / 2
        s5 = p["RS_S1"] / 2000.0
        pts = []
        for j in range(m):
            t = cov * math.sqrt(2) + 0.05 + j * s5
            ox, oy = cc + t / math.sqrt(2), cc + t / math.sqrt(2)
            ux, uy = -1 / math.sqrt(2), 1 / math.sqrt(2)
            v.ln("COTTHEP", ox - ux * hl, oy - uy * hl, ox + ux * hl, oy + uy * hl)
            pts.append(v.P(ox + ux * 0.25 * hl, oy + uy * 0.25 * hl))
        co([pts[0]], v.x(cc + 0.3), v.y(cc - 0.15), 1, 5, f"{g.n5 // 4}%%C{int(d)}")
    # --- thép chủ dầm theo Y (10, 11) trên dầm phải, phía trên dầm X; theo X (13, 14) trên dầm trên, bên phải
    ws = a - 2 * cov - 2 * g.dt
    full_y, cut_y = g.rib_len(True)
    full_x, cut_x = g.rib_len(False)
    nf, nc = g.n_full, g.n_cut
    us_f = [(-ws / 2 + (i + 0.5) * ws / nf) for i in range(nf)]
    us_c = [(-ws / 2 + (i + 0.5) * ws / max(1, nc)) * 0.7 for i in range(nc)]
    y0 = g.dy + a / 2 + g.e
    for u in us_f:
        v.ln("COTTHEP", g.dx + u, y0, g.dx + u, full_y / 2)
    for u in us_c:
        v.ln("COTTHEP", g.dx + u, y0, g.dx + u, cut_y / 2)
    yt = 0.5 * (cut_y / 2 + full_y / 2)
    tl = [v.P(g.dx + u, yt) for u in us_f]
    co(tl, v.x(g.dx + a / 2), v.y(yt), 1, 10, f"{nf}%%C{int(p['RD_D'])}", tick=True, mode=True)
    if nc:
        yc = 0.5 * (y0 + cut_y / 2)
        co([v.P(g.dx + u, yc) for u in us_c], v.x(g.dx + a / 2), v.y(yc), 1, 11,
           f"{nc}%%C{int(p['RD_D'])}", tick=True, mode=True)
    x0 = g.dx + a / 2 + g.e
    for u in us_f:
        v.ln("COTTHEP", x0, g.dy + u, full_x / 2, g.dy + u)
    for u in us_c:
        v.ln("COTTHEP", x0, g.dy + u, cut_x / 2, g.dy + u)
    xt = 0.5 * (cut_x / 2 + full_x / 2)
    co([v.P(xt, g.dy + us_f[-1])], xr, v.y(g.dy) + 4.5, 1, 13, f"{nf}%%C{int(p['RD_D'])}", mode=True)
    if nc:
        co([v.P(0.5 * (x0 + cut_x / 2), g.dy + us_c[0])], xr, v.y(g.dy) - 4.5, 1, 14,
           f"{nc}%%C{int(p['RD_D'])}", mode=True)


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
