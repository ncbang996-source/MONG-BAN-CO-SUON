"""Tờ 2 (TKBVTC): mặt cắt dầm 1-1, 2-2; vát nách 3-3, 4-4; cổ móng 5-5; lưới đầu trụ; 1/2 mặt cắt B-B
(dọc tim dầm theo X, thể hiện thép dầm và neo thép cổ móng); bảng tổng kê."""
from __future__ import annotations

import math

from . import model, tables
from .cad import Ctx
from .geom import ANCHOR, TL_LEG, TL_OUT, TL_W, Geo, ceil_
from .view import V, Callouts, brk, cut_line, dai_draw, note_at, ni, phi, rpl, sym, tie, title

T_MESHH = "LƯỚI THÉP ĐẦU TRỤ"
W_SLAB = 0.75          # bản móng thể hiện mỗi bên dầm trong mặt cắt 1-1, 2-2 (m)


def sc_title(c: Ctx, x, y, s, den):
    title(c, x, y, s, f"TL:1/{den}")


# ---------------------------------------------------------------------------
def rib_section(c: Ctx, g: Geo, co: Callouts, ox, oy, along_y: bool, name: str):
    """Mặt cắt ngang dầm (1-1: dầm theo Y, cắt theo X; 2-2: dầm theo X, cắt theo Y).
    u = 0 tại tim dầm, u < 0 phía ô bản ngoài (2 cạnh ngàm), u > 0 phía ô bản giữa."""
    p = g.p
    v = V(c, ox, oy, 25)
    a, hs, hd, cov, covb = g.a, g.hs, g.hd, g.cov, g.covb
    W = W_SLAB
    ul, ur = -a / 2 - W, a / 2 + W
    tl = model.TL
    # bê tông
    v.pl("MAIN", False, [(ul, hs), (-a / 2, hs), (-a / 2, hd), (a / 2, hd), (a / 2, hs), (ur, hs)])
    v.ln("MAIN", ul, 0.0, ur, 0.0)
    v.rect("HINH THUC", ul, -tl, ur, 0.0)
    v.hatch("HATCH", [(ul, -tl), (ur, -tl), (ur, 0.0), (ul, 0.0)], "AR-CONC", 0.375 * 25 / 100.0)
    for u in (ul, ur):
        brk(c, v.x(u), v.y(-tl), v.x(u), v.y(hs), w=1.2)
    # thép bản
    zYb, zXb, zYt, zXt = g.slab_z()
    if along_y:      # cắt theo X: thanh theo X là đường, thanh theo Y là chấm
        zl_b, zl_t, zd_b, zd_t = zXb, zXt, zYb, zYt
        dots = [x + g.dx for x in g.xs1 if ul < x + g.dx < ur]
        pl_, pd_ = 3, 1
        feet_in = not g.long_x()          # chân thanh chống chạy theo phương cạnh ngắn
        chs = [x + g.dx for x in g.chx if ul + 0.05 < x + g.dx < ur - 0.05]
    else:
        zl_b, zl_t, zd_b, zd_t = zYb, zYt, zXb, zXt
        dots = [y + g.dy for y in g.ys3 if ul < y + g.dy < ur]
        pl_, pd_ = 1, 3
        feet_in = g.long_x()
        chs = [y + g.dy for y in g.chy if ul + 0.05 < y + g.dy < ur - 0.05]
    rs = v.rbar(p["RS_D"])
    v.ln("COTTHEP", ul + 0.02, zl_b, ur - 0.02, zl_b)
    v.ln("COTTHEP", ul + 0.02, zl_t, ur - 0.02, zl_t)
    for u in dots:
        v.disc("COTTHEP", u, zd_b, rs)
        v.disc("COTTHEP", u, zd_t, rs)
    zi_b, zi_t = max(zl_b, zd_b) + g.ds / 2, min(zl_t, zd_t) - g.ds / 2
    rch = v.rbar(p["RCH_D"])
    for u in chs:
        if feet_in:
            xe = 0.1 if u < 0 else -0.1
            v.pl("DAI", False, [(u + xe, zi_b), (u, zi_b), (u, zi_t), (u + xe, zi_t)])
        else:
            v.ln("DAI", u, zi_b, u, zi_t)
            v.disc("DAI", u, zi_b, rch)
            v.disc("DAI", u, zi_t, rch)
    # lồng thép dầm
    w2 = a / 2 - cov
    dai_draw(c, "DAI", v.x(-w2), v.y(covb), v.x(w2), v.y(hd - cov), 0.8, 1.2)
    rm = v.rbar(p["RD_D"])
    for z, row in g.rows_b + g.rows_t:
        for u, _ in row:
            v.disc("COTTHEP", u, z, rm)
    rg = v.rbar(p["RG_D"])
    for z in g.z_gia:
        for s in (-1, 1):
            v.disc("COTTHEP", s * g.u_gia, z, rg)
        tie(c, "DAI", v.x(-g.u_gia - g.dg / 2 - 0.004), v.y(z - g.dg / 2 - 0.004), 1.0, 0.0,
            v.k * (2 * g.u_gia + g.dg + 0.008), 0.35, 1.4)
    if g.has_vtie():
        v.ln("DAI", 0.0, covb + g.dt, 0.0, hd - cov - g.dt)
    # chú thích
    pf, pc, pg = (10, 11, 12) if along_y else (13, 14, 15)
    xr = v.x(ur) + 2.0
    xl = v.x(ul) - 2.0
    rt0 = g.rows_t[0]
    yt = v.y(hd) + 8.0
    full = [(u, rt0[0]) for u, f in rt0[1] if f]
    yt = v.y(hd) + 6.0
    co([v.P(u, z) for u, z in full[-2:]], v.x(a / 2) + 3.0, yt + 5.5, 1, pf,
       f"{len(full)}%%C{ni(p['RD_D'])}", tick=False)
    cut = [(u, z) for z, row in g.rows_t for u, f in row if not f]
    if cut:
        co([v.P(u, z) for u, z in cut[-2:]], v.x(a / 2) + 3.0, yt, 1, pc, f"{len(cut)}%%C{ni(p['RD_D'])}",
           tick=False)
    y16 = v.y(hd) - 3.0
    y12 = min(y16 - 6.0, v.y(g.z_gia[-1]) + 2.0)
    y17 = y12 - 6.0
    co([v.P(w2, 0.5 * (hs + hd) + 0.1)], xr, y16, 1, 16, phi(p["RDT_D"], p["RDT_S"]))
    co([v.P(g.u_gia, g.z_gia[-1])], xr, y12, 1, pg, f"{2 * g.n_gia}%%C{ni(p['RG_D'])}")
    co([v.P(0.25 * g.u_gia, g.z_gia[0] - g.dg / 2)], xr, y17, 1, 17, phi(p["RDP_D"], p["RDP_S"]))
    if g.has_vtie():
        co([v.P(0.0, 0.5 * (hs + hd) + 0.1)], xl, v.y(0.5 * (hs + hd)) + 6.0, -1, 18, phi(p["RDP_D"], p["RDP_S"]))
    # thép bản: trái = ô 2 cạnh ngàm, phải = ô 4 cạnh ngàm
    ds = p["RS_D"]
    dl = [u for u in dots if u < -a / 2]
    dr = [u for u in dots if u > a / 2]
    if len(dl) >= 2:
        co([v.P(dl[-1], zd_t), v.P(dl[-2], zd_t)], xl, v.y(hs) + 4.5, -1, pd_, phi(ds, p["RS_S2"]), tick=False)
    if len(dr) >= 2:
        co([v.P(dr[0], zd_b), v.P(dr[1], zd_b)], xr, v.y(-tl) - 4.0, 1, pd_, phi(ds, p["RS_S1"]), tick=False)
    co([v.P(ul + 0.15, zl_b)], xl, v.y(-tl) - 4.0, -1, pl_, phi(ds, p["RS_S2"]))
    chl = [u for u in chs if u < -a / 2]
    chr_ = [u for u in chs if u > a / 2]
    if chl:
        co([v.P(chl[-1], 0.5 * (zi_b + zi_t))], xl - 2.0, v.y(-tl) - 10.0, -1, 6, phi(p["RCH_D"], p["RCH_S2"]))
    if chr_:
        co([v.P(chr_[0], 0.5 * (zi_b + zi_t))], xr + 2.0, v.y(-tl) - 10.0, 1, 6, phi(p["RCH_D"], p["RCH_S1"]))
    # kích thước
    xd = v.x(ul) - 4.0
    v.dimV((ul, -tl), (ul, 0.0), xd)
    v.dimV((ul, 0.0), (ul, hs), xd)
    v.dimV((-a / 2, hs), (-a / 2, hd), xd)
    v.dimH((-a / 2, hd), (a / 2, hd), v.y(hd) + 3.5)
    sc_title(c, v.x(0.0), v.y(-tl) - 17.0, f"MẶT CẮT {name}", 25)


# ---------------------------------------------------------------------------
def haunch_section(c: Ctx, g: Geo, co: Callouts, ox, oy):
    """3-3: cắt song song mặt vát nách, qua chỗ giao dầm; nhìn về phía cổ móng."""
    p = g.p
    v = V(c, ox, oy, 50)
    a, e, hs, hd, cov = g.a, g.e, g.hs, g.hd, g.cov
    lb = math.sqrt(2) * (2 * a + e) / 2 - math.sqrt(2) * cov      # nửa chiều dài khối dầm trên vết cắt
    W = 0.6
    tl = model.TL
    ul, ur = -lb - W, lb + W
    v.pl("MAIN", False, [(ul, hs), (-lb, hs), (-lb, hd), (lb, hd), (lb, hs), (ur, hs)])
    v.ln("MAIN", ul, 0.0, ur, 0.0)
    v.rect("HINH THUC", ul, -tl, ur, 0.0)
    v.hatch("HATCH", [(ul, -tl), (ur, -tl), (ur, 0.0), (ul, 0.0)], "AR-CONC", 0.375 * 50 / 100.0)
    for u in (ul, ur):
        brk(c, v.x(u), v.y(-tl), v.x(u), v.y(hs), w=1.0)
    # cổ móng phía sau
    bp = g.bb * math.sqrt(2) / 2
    zt = hd + 0.6
    for s in (-1, 1):
        v.ln("MAIN", s * bp, hd, s * bp, zt)
    brk(c, v.x(-bp), v.y(zt), v.x(bp), v.y(zt), w=1.0)
    # thép 7 (U dài), 8 (U ngắn), 9 (đai vuông, các mức)
    l7, l8 = g.l7(), g.l8()
    z7 = hd - cov
    rpl(c, "DAI", [v.P(-l7 / 2, cov), v.P(-l7 / 2, z7), v.P(l7 / 2, z7), v.P(l7 / 2, cov)], False, 0.6)
    z8 = z7 - 0.03
    rpl(c, "DAI", [v.P(-l8 / 2, cov + 0.05), v.P(-l8 / 2, z8), v.P(l8 / 2, z8), v.P(l8 / 2, cov + 0.05)], False, 0.6)
    zs9 = [z8 - 0.05 - i * 0.2 for i in range(g.n9())]
    for z in zs9:
        v.ln("DAI", -l8 / 2 + 0.02, z, l8 / 2 - 0.02, z)
    xr = v.x(ur) + 2.0
    co([v.P(l7 / 2, 0.5 * (hs + hd))], xr, v.y(hd) + 5.0, 1, 7, f"4%%C{ni(p['RDT_D'])}")
    co([v.P(l8 / 2, z8 - 0.12)], xr, v.y(0.5 * (hs + hd)), 1, 8, f"{g.n8()}%%C{ni(p['RDT_D'])}")
    co([v.P(0.25 * l8, z) for z in zs9[:2]], xr, v.y(hs) - 2.5, 1, 9, f"{g.n9()}%%C{ni(p['RDT_D'])}", tick=False)
    xd = v.x(ul) - 4.0
    v.dimV((ul, 0.0), (ul, hs), xd)
    v.dimV((-lb, hs), (-lb, hd), xd)
    # vết cắt 4-4 (mặt bằng tại cao độ giữa dầm)
    zm = 0.5 * (hs + hd) + 0.05
    cut_line(c, v.P(-lb - 0.15, zm), v.P(lb + 0.15, zm), "4", side=-1.0, ext=1.0)
    sc_title(c, v.x(0.0), v.y(-tl) - 9.0, "MẶT CẮT 3-3", 50)


def haunch_plan(c: Ctx, g: Geo, co: Callouts, ox, oy):
    """4-4: mặt bằng tại chỗ giao dầm - thép vát nách 7, 8, 9 và thép chủ cổ móng."""
    p = g.p
    v = V(c, ox, oy, 50)
    a, e, cov = g.a, g.e, g.cov
    R = a / 2 + e + 0.45
    h = a / 2
    # mép dầm + vát
    for sx in (-1, 1):
        for sy in (-1, 1):
            v.pl("MAIN", False, [(sx * R, sy * h), (sx * (h + e), sy * h), (sx * h, sy * (h + e)), (sx * h, sy * R)])
    for s in (-1, 1):
        brk(c, v.x(s * R), v.y(-h - 0.1), v.x(s * R), v.y(h + 0.1), w=1.0)
        brk(c, v.x(-h - 0.1), v.y(s * R), v.x(h + 0.1), v.y(s * R), w=1.0)
    v.ln("TRUC", -R - 0.2, 0.0, R + 0.2, 0.0)
    v.ln("TRUC", 0.0, -R - 0.2, 0.0, R + 0.2)
    r2 = 1 / math.sqrt(2)
    # 7: dọc 4 mặt vát
    l7, l8 = g.l7(), g.l8()
    d7 = (a + e) / 2 - cov
    p7 = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            mx, my = sx * d7, sy * d7
            ux, uy = -sx * r2, sy * r2
            v.ln("DAI", mx - ux * l7 / 2, my - uy * l7 / 2, mx + ux * l7 / 2, my + uy * l7 / 2)
            p7.append(v.P(mx + ux * 0.42 * l7, my + uy * 0.42 * l7))
    # 9: đai vuông (hình thoi cạnh l8)
    rr = l8 * r2
    v.pl("DAI", True, [(rr, 0.0), (0.0, rr), (-rr, 0.0), (0.0, -rr)])
    # 8: 2 họ song song các cạnh thoi
    n8 = g.n8()
    p8 = []
    for fam in (1, -1):
        for i in range(n8):
            t = -rr + (i + 1) * 2 * rr / (n8 + 1)
            # đường x + fam*y = t*... (song song cạnh thoi), trong thoi
            ux, uy = (-r2, r2) if fam == 1 else (r2, r2)
            nx, ny = (r2, r2) if fam == 1 else (r2, -r2)
            mx, my = nx * t * r2, ny * t * r2
            v.ln("DAI", mx - ux * l8 / 2, my - uy * l8 / 2, mx + ux * l8 / 2, my + uy * l8 / 2)
            if i == n8 - 1:
                p8.append(v.P(mx + ux * 0.3 * l8, my + uy * 0.3 * l8))
    # thép chủ cổ móng (chấm)
    hb = g.bb / 2 - cov - g.g("RC_D") / 2000.0
    m = g.m_bars()
    rc = v.rbar(p["RC_D"])
    for i in range(m):
        t = -hb + i * 2 * hb / (m - 1)
        for q in ((t, -hb), (t, hb), (-hb, t), (hb, t)):
            v.disc("COTTHEP", q[0], q[1], rc)
    xr = v.x(R) + 3.0
    co([p7[3]], xr, v.y(R) - 2.0, 1, 7, f"4%%C{ni(p['RDT_D'])}")
    co(p8, xr, v.y(0.3 * R), 1, 8, f"{2 * n8}%%C{ni(p['RDT_D'])}")
    co([v.P(rr * 0.5, -rr * 0.5)], xr, v.y(-0.55 * R), 1, 9, phi(p["RDT_D"], 200))
    v.dimH((-h - e, h), (-h, h), v.y(R) + 3.5)
    v.dimH((-h, h), (h, h), v.y(R) + 3.5)
    v.dimH((h, h), (h + e, h), v.y(R) + 3.5)
    sc_title(c, v.x(0.0), v.y(-R) - 9.0, "MẶT CẮT 4-4", 50)


# ---------------------------------------------------------------------------
def pier_section(c: Ctx, g: Geo, co: Callouts, cx, cy):
    """5-5: mặt cắt ngang cổ móng (thép chủ 19, đai 20, đai phụ 21, đai bát giác 22, thang leo 24)."""
    p = g.p
    kk, cov = 40.0, p["COVER"]
    hh = kk * p["BB"] / 2
    c.rect("MAIN", cx - hh, cy - hh, cx + hh, cy + hh)
    hb = hh - kk * cov
    hb0 = hb
    dai_draw(c, "DAI", cx - hb, cy - hb, cx + hb, cy + hb, 1.0, 1.3)
    n = int(p["RC_N"])
    m = 1 + int(n / 4.0)
    dia = p["RC_D"]
    r = max(0.35, 0.5 * dia / 1000.0 * kk)
    hb = hb - 0.2 - r
    lst = []
    for i in range(m):
        x = -hb + i * 2 * hb / (m - 1)
        lst += [(x, -hb), (x, hb)]
        if 0 < i < m - 1:
            lst += [(-hb, x), (hb, x)]
    for px, py in lst:
        c.disc("COTTHEP", cx + px, cy + py, r)
    grp, st = g.tie_plan()
    rt = r + 0.12
    for i in st:
        x = -hb + i * 2 * hb / (m - 1)
        tie(c, "DAI", cx + x + rt, cy - hb, 0.0, 1.0, 2 * hb, rt, 2.2)
        tie(c, "DAI", cx - hb, cy + x - rt, 1.0, 0.0, 2 * hb, rt, 2.2)
    xo = yo = None
    if grp:
        i = max(grp)
        xo = abs(-hb + i * 2 * hb / (m - 1)) + 0.41421356 * rt
        yo = hb + rt
        c.pl("DAI", True, [(cx - xo, cy + yo), (cx + xo, cy + yo), (cx + yo, cy + xo), (cx + yo, cy - xo),
                           (cx + xo, cy - yo), (cx - xo, cy - yo), (cx - yo, cy - xo), (cx - yo, cy + xo)])
    bx = cx + hh + 5.0
    sp = 2 * hb / (m - 1)
    co([(cx - hb + i * sp, cy + hb) for i in range(m)], bx, cy + hh + 5.0, 1, 19,
       f"{m}%%C{ni(dia)}", tick=False, mode=True)
    co([(cx + hb0, cy + 0.55 * hh)], bx, cy + 0.55 * hh, 1, 20, phi(p["RT_D"], p["RT_S"]), mode=True)
    if st:
        xi = -hb + max(st) * sp
        co([(cx + xi + rt, cy + 0.15 * hh)], bx, cy + 0.15 * hh, 1, 21, phi(p["RP_D"], p["RP_S"]), mode=True)
    if grp:
        co([(cx + 0.5 * (xo + yo), cy - 0.5 * (xo + yo))], bx, cy - 0.45 * hh, 1, 22,
           phi(p["RP_D"], p["RP_S"]), mode=True)
    # thang leo: bậc chữ U nhô ra mặt trái cổ móng
    if g.n_ladder():
        lg, wd, out = kk * TL_LEG, kk * TL_W, kk * TL_OUT
        xf = cx - hh
        rpl(c, "COTTHEP", [(xf + lg, cy - wd / 2), (xf - out, cy - wd / 2), (xf - out, cy + wd / 2),
                           (xf + lg, cy + wd / 2)], False, 0.6)
        co([(xf - out, cy + 0.2 * wd)], xf - out - 2.0, cy - hh - 3.0, -1, 24, phi(p["TL_D"], p["TL_S"]))
        from .cad import ensure_dimstyle
        nm = ensure_dimstyle(c.doc, 25)
        c.dimV("DIM", (xf - out, cy - hh), (xf, cy - hh), xf - out - 3.0, dimname=nm)
    from .cad import ensure_dimstyle
    nm = ensure_dimstyle(c.doc, 25)
    c.dimH("DIM", (cx - hh, cy + hh), (cx + hh, cy + hh), cy + hh + 9.5, dimname=nm)
    c.dimV("DIM", (cx + hh, cy - hh), (cx + hh, cy + hh), cx + hh + 3.5, dimname=nm)
    sc_title(c, cx, cy - hh - 11.0, "MẶT CẮT 5-5", 25)


def mesh(c: Ctx, g: Geo, co: Callouts, cx, cy):
    p = g.p
    kk = 40.0
    hh = kk * p["BB"] / 2
    c.rect("MAIN", cx - hh, cy - hh, cx + hh, cy + hh)
    hb = hh - kk * p["COVER"]
    s = kk * p["RL_S"] / 1000.0
    n = ceil_(2 * hb / s - 1e-6)
    for i in range(n + 1):
        t = -hb + i * 2 * hb / n
        c.ln("DAI", cx - hb, cy + t, cx + hb, cy + t)
        c.ln("DAI", cx + t, cy - hb, cx + t, cy + hb)
    co([(cx + hb, cy + 3.0)], cx + hh + 5.0, cy + 3.0, 1, 23, phi(p["RL_D"], p["RL_S"]), f"({int(p['RL_N'])} LỚP)")
    from .cad import ensure_dimstyle
    nm = ensure_dimstyle(c.doc, 25)
    c.dimH("DIM", (cx - hh, cy - hh), (cx + hh, cy - hh), cy - hh - 4.5, dimname=nm)
    c.dimV("DIM", (cx - hh, cy - hh), (cx - hh, cy + hh), cx - hh - 4.5, dimname=nm)
    sc_title(c, cx, cy - hh - 12.0, T_MESHH, 25)


# ---------------------------------------------------------------------------
def bb_scale(g: Geo):
    for d in (50, 75, 100, 125, 150):
        k = 1000.0 / d
        if k * g.Lh <= 122.0 and k * (g.H + model.TL) <= 105.0:
            return d
    return 150


def half_bb(c: Ctx, g: Geo, co: Callouts, xax, ytop):
    """1/2 mặt cắt B-B: cắt dọc tim dầm theo X (y = +L2/2), nửa trái (x <= 0), nhìn theo +Y."""
    p = g.p
    den = bb_scale(g)
    k = 1000.0 / den
    v = V(c, xax, ytop - k * g.H, den)
    L, hd, cov, covb = g.Lh, g.hd, g.cov, g.covb
    tl, ml = model.TL, model.ML
    bb = g.bb
    px = -g.dx
    # bê tông
    v.pl("MAIN", False, [(0.0, 0.0), (-L, 0.0), (-L, hd), (px - bb / 2, hd), (px - bb / 2, g.H), (px + bb / 2, g.H),
                         (px + bb / 2, hd), (0.0, hd)])
    v.rect("HINH THUC", -L - ml, -tl, 0.0, 0.0)
    v.hatch("HATCH", [(-L - ml, -tl), (0.0, -tl), (0.0, 0.0), (-L - ml, 0.0)], "AR-CONC", 0.375 * den / 100.0)
    v.ln("TRUC", 0.0, -tl - 0.15, 0.0, g.H + 0.3)
    v.ln("TRUC", px, -tl - 0.15, px, g.H + 0.3)
    sym(c, v.x(0.0), v.y(g.H) - 0.5)
    # thép chủ dầm theo X (13 dài suốt, 14 ngắt), thép giá (15)
    full, cut = g.rib_len(False)
    for z, row in g.rows_b + g.rows_t:
        if any(f for _, f in row):
            v.ln("COTTHEP", -full / 2, z, 0.0, z)
        if any(not f for _, f in row):
            v.ln("COTTHEP", -cut / 2, z, 0.0, z)
    for z in g.z_gia:
        v.ln("COTTHEP", -full / 2, z, 0.0, z)
    # đai dầm (16)
    sts = [s for s in g.stirrups(False) if s <= 1e-9]
    for s in sts:
        v.ln("DAI", s, covb, s, hd - cov)
    # đai vuông vát nách (9) tại chỗ giao dầm
    if g.hasHaunch:
        rr = g.l8() / math.sqrt(2)
        for i in range(g.n9()):
            z = hd - cov - 0.08 - i * 0.2
            v.ln("DAI", px - rr, z, px + rr, z)
    # thép bản theo Y (chấm) chạy dưới đáy dầm
    zYb, zXb, zYt, zXt = g.slab_z()
    rs = v.rbar(p["RS_D"])
    for x in g.xs1:
        if x < 0:
            v.disc("COTTHEP", x, zYb, rs)
    # cổ móng: thép chủ 19 (neo chân 500 vào bản), đai 20, lưới 23
    zt = g.H - cov
    zb = covb + 2 * g.ds
    xi = bb / 2 - cov - g.g("RC_D") / 2000.0
    for s in (-1, 1):
        v.pl("COTTHEP", False, [(px + s * xi, zt), (px + s * xi, zb), (px + s * (xi + ANCHOR), zb)])
    for z in g.hoop_zs():
        v.ln("DAI", px - xi, z, px + xi, z)
    s_l = p["RL_S"] / 1000.0
    rl = v.rbar(p["RL_D"])
    for il in range(int(p["RL_N"])):
        z = zt - 0.02 - il * s_l
        v.ln("DAI", px - xi, z, px + xi, z)
        nd = ceil_(2 * xi / s_l - 1e-6)
        for j in range(nd + 1):
            v.disc("DAI", px - xi + j * 2 * xi / nd, z - 0.015, rl)
    # thang leo (24) ở mặt cổ quay vào tim
    nl = g.n_ladder()
    if nl:
        s = p["TL_S"] / 1000.0
        xf = px + bb / 2
        for i in range(nl):
            z = zt - i * s
            v.ln("COTTHEP", xf - TL_LEG, z, xf + TL_OUT, z)
    # vết cắt 5-5 trên cổ móng
    zc = hd + 0.3 * (g.H - hd)
    cut_line(c, v.P(px - bb / 2 - 0.1, zc), v.P(px + bb / 2 + TL_OUT + 0.1, zc), "5", side=-1.0, ext=1.5)
    # chú thích (trong khoảng trống phía trên dầm)
    d = p["RD_D"]
    xa = v.x(px - bb / 2) - 2.0
    ztop = g.rows_t[0][0]
    co([v.P(-L + 0.4, ztop)], v.x(-L) + 1.0, v.y(hd) + 7.0, 1, 13, f"{2 * g.n_full}%%C{ni(d)}")
    if g.n_cut:
        z2 = g.rows_t[1][0] if len(g.rows_t) > 1 else ztop
        co([v.P(-cut / 2 + 0.3, z2)], v.x(-L) + 1.0, v.y(hd) + 13.0, 1, 14, f"{2 * g.n_cut}%%C{ni(d)}")
    co([v.P(-L + 0.9, g.z_gia[0])], v.x(-L) + 1.0, v.y(hd) + 19.0, 1, 15, f"{2 * g.n_gia}%%C{ni(p['RG_D'])}")
    if sts:
        co([v.P(sts[2], 0.5 * (hd + g.z_gia[0]))], v.x(-L) + 1.0, v.y(hd) + 25.0, 1, 16,
           phi(p["RDT_D"], p["RDT_S"]))
    xr = v.x(px + bb / 2 + TL_OUT) + 4.0
    hz = g.hoop_zs()
    co([v.P(px + xi, zt - 0.35 * (zt - hd))], xr, v.y(zt) - 6.0, 1, 19,
       f"{int(p['RC_N'])}%%C{ni(p['RC_D'])}")
    zh = hz[len(hz) // 2]
    co([v.P(px, zh)], xr, v.y(zt) - 13.0, 1, 20, phi(p["RT_D"], p["RT_S"]))
    co([v.P(px + xi, zt - 0.02)], xr, v.y(zt) + 2.0, 1, 23, phi(p["RL_D"], p["RL_S"]))
    if nl:
        z = zt - (nl // 2) * p["TL_S"] / 1000.0
        co([v.P(px + bb / 2 + TL_OUT, z)], xr, v.y(zt) - 20.0, 1, 24, phi(p["TL_D"], p["TL_S"]))
    # kích thước
    yd = v.y(-tl) - 5.0
    v.dimH((-L, 0.0), (px - bb / 2, 0.0), yd)
    v.dimH((px - bb / 2, 0.0), (px + bb / 2, 0.0), yd)
    v.dimH((px + bb / 2, 0.0), (0.0, 0.0), yd)
    xd = v.x(-L - ml) - 4.0
    v.dimV((-L, 0.0), (-L, hd), v.x(-L) - 3.5)
    v.dimV((px - bb / 2, hd), (px - bb / 2, g.H), xa - 1.0)
    v.dimV((-L - ml, -tl), (-L - ml, 0.0), xd)
    sc_title(c, v.x(-L / 2), yd - 10.0, "1/2 MẶT CẮT B-B", den)
    return yd - 16.0


# ---------------------------------------------------------------------------
def draw(c: Ctx, g: Geo):
    if not getattr(g, "kl", None):
        g.calc_kl()
    co = Callouts(c, g)
    with c.group("bb", "1/2 Mặt cắt B-B"):
        ybb = half_bb(c, g, co, 392.0, 266.0)
    oy1 = 258.0 - 40.0 * g.hd
    oy2 = oy1 - (40.0 * g.hd + 50.0)
    oy3 = min(52.0, oy2 - 36.0 - 20.0 * (g.hd + 0.6))
    with c.group("sec11", "Mặt cắt 1-1"):
        rib_section(c, g, co, 88.0, oy1, True, "1-1")
    with c.group("sec22", "Mặt cắt 2-2"):
        rib_section(c, g, co, 88.0, oy2, False, "2-2")
    if g.hasHaunch:
        with c.group("sec33", "Mặt cắt 3-3"):
            haunch_section(c, g, co, 82.0, oy3)
        with c.group("sec44", "Mặt cắt 4-4"):
            haunch_plan(c, g, co, 200.0, 62.0)
    with c.group("mesh", "Lưới thép đầu trụ"):
        mesh(c, g, co, 202.0, 246.0)
    with c.group("sec55", "Mặt cắt 5-5"):
        pier_section(c, g, co, 202.0, 165.0)
    tables.summary(c, g, 405.0, 98.0)
    note_at(c, 268.0, min(ybb, 125.0), ["- XEM GHI CHÚ CHUNG TẠI BẢN VẼ SỐ: " + str(g.p.get("CODE", "")),
                                         "- KÍCH THƯỚC GHI TRÊN BẢN VẼ TÍNH BẰNG mm."])
