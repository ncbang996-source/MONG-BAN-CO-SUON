"""Tờ 2 (TKBVTC): mặt cắt dầm 1-1, 2-2; vát nách 3-3, 4-4; cổ móng 5-5; lưới đầu trụ; 1/2 mặt cắt B-B
(dọc tim dầm theo X, thể hiện thép dầm và neo thép cổ móng); bảng tổng kê."""
from __future__ import annotations

import math

from . import model, tables
from .cad import Ctx
from .geom import ANCHOR, TL_LEG, TL_OUT, TL_W, Geo, ceil_
from .view import V, Callouts, brk, cut_line, dai_draw, note_at, ni, phi, rpl, sym, tick45, tie, title

T_MESHH = "LƯỚI THÉP ĐẦU TRỤ"
W_SLAB = 0.75          # bản móng thể hiện mỗi bên dầm trong mặt cắt 1-1, 2-2 (m)
LOT_HATCH = 0.9        # tỷ lệ hatch bê tông lót trong các mặt cắt chi tiết (thưa, mảnh)


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
    v.hatch("HATCH", [(ul, -tl), (ur, -tl), (ur, 0.0), (ul, 0.0)], "AR-CONC", LOT_HATCH * 25 / 100.0)
    for u in (ul, ur):
        brk(c, v.x(u), v.y(-tl), v.x(u), v.y(hs), w=1.2)
    # thép bản (thanh ngang chạm nét ziczac)
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
    v.ln("COTTHEP", ul, zl_b, ur, zl_b)
    v.ln("COTTHEP", ul, zl_t, ur, zl_t)
    for u in dots:
        v.disc("COTTHEP", u, zd_b, rs)
        v.disc("COTTHEP", u, zd_t, rs)
    zi_b, zi_t = max(zl_b, zd_b) + g.ds / 2, min(zl_t, zd_t) - g.ds / 2
    rch = v.rbar(p["RCH_D"])
    # thanh chống đặt kẹp sát 1 thanh thép bản (chấm tròn)
    gap = (p["RS_D"] + p["RCH_D"]) / 2000.0
    moved = []
    for u in chs:
        if dots:
            dd = min(dots, key=lambda q: abs(q - u))
            sd = 1.0 if u >= dd else -1.0
            nu = dd + sd * gap
            if not (ul < nu < ur) or (-a / 2 - 0.02 < nu < a / 2 + 0.02):
                nu = dd - sd * gap
            u = nu
        if all(abs(u - q) > 1e-6 for q in moved):
            moved.append(u)
    chs = moved
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
    rg = v.rbar(p["RS_D"])
    for z in g.z_gia:
        for s in (-1, 1):
            v.disc("COTTHEP", s * g.u_gia, z, rg)
        tie(c, "DAI", v.x(-g.u_gia - g.dg / 2 - 0.004), v.y(z - g.dg / 2 - 0.004), 1.0, 0.0,
            v.k * (2 * g.u_gia + g.dg + 0.008), 0.35, 1.4)
    if g.has_vtie():
        v.ln("DAI", 0.0, covb + g.dt, 0.0, hd - cov - g.dt)
    um = g.u_tie2()
    zt2 = g.z_tie2()             # đai phụ giữ lớp thép 2: ngay dưới hàng lớp 2, móc ôm 2 thanh biên
    rh = rm + 0.12
    for z in zt2:
        tie(c, "DAI", v.x(-um), v.y(z), 1.0, 0.0, v.k * 2 * um, rh, 1.4)
    # chú thích: thép chủ - gióng vuông góc tới từng thanh (không xẹt); đai - leader ngang có xẹt 45°
    pf, pc, pg = (10, 11, 12) if along_y else (13, 14, 15)
    xr = v.x(ur) + 2.0
    xl = v.x(ul) - 2.0
    dmm = ni(p["RD_D"])
    rt0 = g.rows_t[0]
    full = [u for u, f in rt0[1] if f]
    co([v.P(u, rt0[0]) for u in full], v.x(-a / 2) - 1.0, v.y(hd) + 6.0, -1, pf, f"{len(full)}%%C{dmm}",
       tick=False, mode=True)
    v.dimH((-a / 2, hd), (a / 2, hd), v.y(hd) + 11.5)
    # bên phải, từ trên xuống
    yprev = v.y(hd) + 2.0
    cut = [(u, z) for z, row in g.rows_t for u, f in row if not f]
    if cut:                      # thanh ngắt lớp 2: gióng từ dưới lên
        by = v.y(cut[0][1]) - 2.5
        co([v.P(u, z) for u, z in cut], xr, by, 1, pc, f"{len(cut)}%%C{dmm}", tick=False, mode=True)
        yprev = by
    by = yprev - 6.0
    co([(v.x(w2), by)], xr, by, 1, 16, phi(p["RDT_D"], p["RDT_S"]), mode=True)
    yprev = by
    if g.n_gia:                  # thép giá: đường ngang dưới 2 chấm, gióng vuông góc lên (như tag 10, 11)
        by = min(v.y(g.z_gia[-1]) - 2.5, yprev - 6.0)
        co([v.P(s_ * g.u_gia, g.z_gia[-1]) for s_ in (-1, 1)], xr, by, 1, pg, f"{2 * g.n_gia}%%C{ni(p['RS_D'])}",
           tick=False, mode=True)
        yprev = by
    zt17 = sorted([z - g.dg / 2 - 0.004 for z in g.z_gia] + zt2, reverse=True)
    if zt17:                     # đai phụ ngang: 1 leader đứng qua mọi vị trí (thép giá + giữ lớp 2)
        by = yprev - 6.0
        u17 = 0.3 * (um if um else g.u_gia)
        co([v.P(u17, z) for z in zt17], xr, by, 1, 17, phi(p["RDP_D"], p["RDP_S"]), mode=True)
    if g.has_vtie():
        zm = 0.5 * (hs + hd)
        co([v.P(0.0, zm)], v.x(-a / 2) - 1.0, v.y(zm), -1, 18, phi(p["RDP_D"], p["RDP_S"]), mode=True)
    # thép bản: trái = ô 2 cạnh ngàm, phải = ô 4 cạnh ngàm
    ds = p["RS_D"]
    dl = [u for u in dots if u < -a / 2]
    dr = [u for u in dots if u > a / 2]
    if len(dl) >= 2:
        co([v.P(dl[0], zd_t), v.P(dl[1], zd_t)], v.x(dl[0]) - 1.0, v.y(hs) + 4.5, -1, pd_, phi(ds, p["RS_S2"]),
           tick=False)
    if len(dr) >= 2:
        co([v.P(dr[-1], zd_b), v.P(dr[-2], zd_b)], v.x(dr[-1]) + 1.0, v.y(-tl) - 4.0, 1, pd_, phi(ds, p["RS_S1"]),
           tick=False)
    co([v.P(ul + 0.12, zl_b), v.P(ul + 0.12, zl_t)], xl, v.y(-tl) - 4.0, -1, pl_, phi(ds, p["RS_S2"]), mode=True)
    chl = [u for u in chs if u < -a / 2]
    chr_ = [u for u in chs if u > a / 2]
    if chl:
        co([v.P(chl[0], 0.5 * (zi_b + zi_t))], xl, v.y(-tl) - 10.0, -1, 6, phi(p["RCH_D"], p["RCH_S2"]))
    if chr_:
        co([v.P(chr_[-1], 0.5 * (zi_b + zi_t))], xr, v.y(-tl) - 10.0, 1, 6, phi(p["RCH_D"], p["RCH_S1"]))
    # kích thước
    xd = v.x(ul) - 4.0
    v.dimV((ul, -tl), (ul, 0.0), xd)
    v.dimV((ul, 0.0), (ul, hs), xd)
    v.dimV((-a / 2, hs), (-a / 2, hd), xd)
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
    v.hatch("HATCH", [(ul, -tl), (ur, -tl), (ur, 0.0), (ul, 0.0)], "AR-CONC", LOT_HATCH * 50 / 100.0)
    for u in (ul, ur):
        brk(c, v.x(u), v.y(-tl), v.x(u), v.y(hs), w=1.0)
    # cổ móng phía sau
    bp = g.bb * math.sqrt(2) / 2
    zt = hd + 0.6
    for s in (-1, 1):
        v.ln("MAIN", s * bp, hd, s * bp, zt)
    brk(c, v.x(-bp), v.y(zt), v.x(bp), v.y(zt), w=1.0)
    # 7: chữ U ôm ngoài; 8: chân đứng của họ thanh vuông góc mặt cắt; 9: các mức đai vuông (nét ngang)
    l7, l8 = g.l7(), g.l8()
    z7 = hd - cov
    rpl(c, "DAI", [v.P(-l7 / 2, cov), v.P(-l7 / 2, z7), v.P(l7 / 2, z7), v.P(l7 / 2, cov)], False, 0.6)
    n8 = g.n8()
    u8 = [-l8 / 2 + (i + 1) * l8 / (n8 + 1) for i in range(n8)]
    z8 = z7 - g.dt - 0.02
    for u in u8:
        v.ln("DAI", u, cov, u, z8)
    zs9 = [z8 - 0.03 - i * 0.2 for i in range(g.n9())]
    for z in zs9:
        v.ln("DAI", -l8 / 2, z, l8 / 2, z)
    xr = v.x(ur) + 2.0
    co([v.P(l7 / 2 - 0.1, z7)], xr, v.y(hd) + 4.0, 1, 7, f"4%%C{ni(p['RDT_D'])}", mode=True)
    # leader nằm giữa 2 mức đai để không trùng nét
    zm = [0.5 * (zs9[i] + zs9[i + 1]) for i in range(len(zs9) - 1)] or [zs9[0] - 0.1]
    zt8 = zm[0]
    co([v.P(u, zt8) for u in u8], xr, v.y(zt8), 1, 8, f"{n8}%%C{ni(p['RDT_D'])}", mode=True)
    u9 = 0.5 * (u8[len(u8) // 2 - 1] + u8[len(u8) // 2]) if len(u8) > 1 else 0.15
    z9 = zm[2] if len(zm) > 2 else zs9[-1] - 0.1
    co([v.P(u9, z) for z in zs9], xr, min(v.y(z9), v.y(zt8) - 6.0), 1, 9, f"{g.n9()}%%C{ni(p['RDT_D'])}", mode=True)
    xd = v.x(ul) - 4.0
    v.dimV((ul, -tl), (ul, 0.0), xd)
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
    # 7: dọc 4 mặt vát, kéo dài qua góc hình thoi (thấy dạng chữ X ở 4 đỉnh)
    l7, l8 = g.l7(), g.l8()
    d7 = (a + e) / 2 - cov
    tips = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            mx, my = sx * d7, sy * d7
            ux, uy = -sx * r2, sy * r2
            v.ln("DAI", mx - ux * l7 / 2, my - uy * l7 / 2, mx + ux * l7 / 2, my + uy * l7 / 2)
            for t in (-1, 1):
                tips.append((mx + t * ux * l7 / 2, my + t * uy * l7 / 2))
    # 8: 2 họ thanh song song các cạnh thoi, nằm trong thoi
    n8 = g.n8()
    fams = []
    for fam in (1, -1):
        ux, uy = (-r2, r2) if fam == 1 else (r2, r2)
        nx, ny = (r2, r2) if fam == 1 else (r2, -r2)
        ts = [-l8 / 2 + (i + 1) * l8 / (n8 + 1) for i in range(n8)]
        for t in ts:
            mx, my = nx * t, ny * t
            v.ln("DAI", mx - ux * l8 / 2, my - uy * l8 / 2, mx + ux * l8 / 2, my + uy * l8 / 2)
        fams.append((nx, ny, ux, uy, ts))
    xr = v.x(R) + 3.0
    top = sorted(tips, key=lambda q: -q[1])[:2]
    yb = max(q[1] for q in top)
    co([v.P(*q) for q in top], xr, v.y(yb) - 2.0, 1, 7, f"4%%C{ni(p['RDT_D'])}", tick=False)   # 2 đường xiên chụm lại
    # chú thích họ thanh 8 (theo bản vẽ mẫu): đường mảnh vuông góc cắt qua cả họ, xẹt tại từng thanh, nối ra tag
    for (nx, ny, ux, uy, ts), yt in zip(fams, (0.35 * R, -0.5 * R)):
        o = 0.25 * l8 * (1 if ny > 0 else -1)
        p1 = (nx * (ts[0] - 0.08) + ux * o, ny * (ts[0] - 0.08) + uy * o)
        p2 = (nx * (ts[-1] + 0.08) + ux * o, ny * (ts[-1] + 0.08) + uy * o)
        with c.item(f"cross8{int(ny > 0)}", "Đường gióng thép 8"):
            v.ln("CHU", p1[0], p1[1], p2[0], p2[1])
            for t in ts:
                q = v.P(nx * t + ux * o, ny * t + uy * o)
                tick45(c, q[0], q[1])
        co([v.P(*p2)], xr, v.y(yt), 1, 8, f"{n8}%%C{ni(p['RDT_D'])}", tick=False)
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
       f"{n}%%C{ni(dia)}", tick=False, mode=True)
    co([(cx + hb0, cy + 0.55 * hh)], bx, cy + 0.55 * hh, 1, 20, phi(p["RT_D"], p["RT_S"]), mode=True)
    if st:
        xi = -hb + max(st) * sp
        sole = sorted(st) != sorted(m - 1 - j for j in st)         # đai phụ không đối xứng
        # chỉ vào cả 2 thanh đai phụ (phương đứng và phương ngang)
        yv = cy - 0.45 * hh
        co([(cx + xi + rt, yv), (cx + 0.55 * hb, cy + xi - rt)], bx, yv, 1, 21, phi(p["RP_D"], p["RP_S"]),
           "SO LE" if sole else None, mode=True)
    if grp:
        co([(cx + 0.5 * (xo + yo), cy - 0.5 * (xo + yo))], bx, cy - 0.8 * hh, 1, 22,
           phi(p["RP_D"], p["RP_S"]), mode=True)
    # thang leo: bậc chữ U nhô ra mặt trái cổ móng
    if g.n_ladder():
        lg, wd, out = kk * TL_LEG, kk * TL_W, kk * TL_OUT
        xf = cx - hh
        rpl(c, "COTTHEP", [(xf + lg, cy - wd / 2), (xf - out, cy - wd / 2), (xf - out, cy + wd / 2),
                           (xf + lg, cy + wd / 2)], False, 0.6)
        yt = cy - wd / 2 + 1.0
        co([(xf - out, yt)], xf - out, yt, -1, 24, phi(p["TL_D"], p["TL_S"]), mode=True)
        from .cad import ensure_dimstyle
        nm = ensure_dimstyle(c.doc, 25)
        c.dimH("DIM", (xf - out, cy + wd / 2), (xf, cy + wd / 2), cy + wd / 2 + 3.0, dimname=nm)
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
    v.hatch("HATCH", [(-L - ml, -tl), (0.0, -tl), (0.0, 0.0), (-L - ml, 0.0)], "AR-CONC", LOT_HATCH * den / 100.0)
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
    s_tl = p["TL_S"] / 1000.0
    zs_tl = [zt - i * s_tl for i in range(nl)]
    xf = px + bb / 2
    for z in zs_tl:
        v.ln("COTTHEP", xf - TL_LEG, z, xf + TL_OUT, z)
    # vết cắt 5-5 trên cổ móng
    zc = hd + 0.3 * (g.H - hd)
    cut_line(c, v.P(px - bb / 2 - 0.1, zc), v.P(px + bb / 2 + TL_OUT + 0.1, zc), "5", side=-1.0, ext=1.5)
    # chú thích - leader vuông góc
    d = p["RD_D"]

    def gap_x(x):
        """Hoành độ giữa 2 đai dầm gần x nhất (không trùng nét đai)."""
        st = sorted(sts)
        best = x
        for i in range(len(st) - 1):
            m_ = 0.5 * (st[i] + st[i + 1])
            if abs(m_ - x) < abs(best - x) or best == x:
                best = m_
        return best
    xe = v.x(-L) + 2.0
    # 13, 14: kiểu đường kích thước - gióng đứng nối thanh dưới với thanh trên, xẹt 2 đầu
    x13 = gap_x(-L + 0.4)
    co([v.P(x13, g.rows_t[0][0]), v.P(x13, g.rows_b[0][0])], xe, v.y(hd) + 6.0, -1, 13,
       f"{2 * g.n_full}%%C{ni(d)}", mode=True)
    if g.n_cut and len(g.rows_t) > 1:
        x14 = gap_x(max(-cut / 2 + 0.3, x13 + 0.5))
        co([v.P(x14, g.rows_t[1][0]), v.P(x14, g.rows_b[1][0])], xe, v.y(hd) + 12.0, -1, 14,
           f"{2 * g.n_cut}%%C{ni(d)}", mode=True)
    else:
        x14 = x13
    x15 = gap_x(x14 + 0.4)
    if g.n_gia:
        co([v.P(x15, g.z_gia[0])], xe, v.y(hd) + 18.0, -1, 15, f"{2 * g.n_gia}%%C{ni(p['RS_D'])}", mode=True)
    # 16: đường ngang cắt qua 3 đai, có xẹt
    s16 = sorted(sts)[1:4]
    if s16:
        z16 = g.rows_b[-1][0] + g.dm / 2 + 0.06          # thấp, tránh chữ kích thước chiều cao dầm
        co([v.P(x, z16) for x in s16], v.x(-L - ml) - 9.0, v.y(z16), -1, 16, phi(p["RDT_D"], p["RDT_S"]),
           mode=True)
    # cổ móng: chú thích bên trái cổ, đặt ở khoảng hở giữa 2 đai; thang leo bên phải
    xp = v.x(px - bb / 2) - 2.0
    nd = ceil_(2 * xi / s_l - 1e-6)
    jd = nd // 2
    ym = [v.P(px - xi + jd * 2 * xi / nd, zt - 0.02 - il * s_l - 0.015) for il in range(min(2, int(p["RL_N"])))]
    co(ym, xp, v.y(zt) + 1.0, -1, 23, phi(p["RL_D"], p["RL_S"]), tick=False, mode=False)
    hz = sorted(g.hoop_zs(), reverse=True)
    gaps = [0.5 * (hz[i] + hz[i + 1]) for i in range(len(hz) - 1)]
    zl = zt - 0.02 - (int(p["RL_N"]) - 1) * s_l - 0.06       # dưới lưới đầu trụ
    gaps = [z for z in gaps if z < zl and v.y(z) <= v.y(zt) + 1.0 - 6.5] or gaps   # cách tag lưới >= 6.5 mm
    z19 = gaps[0]
    y19 = v.y(z19)
    co([(v.x(px - xi), y19), (v.x(px + xi), y19)], xp, y19, -1, 19, f"{int(p['RC_N'])}%%C{ni(p['RC_D'])}",
       mode=True)
    if len(gaps) > 3:
        z20 = gaps[3]
        sel = [z for z in hz if z < z20][:3]
        co([v.P(px - 0.55 * xi, z) for z in sel], xp, v.y(z20), -1, 20, phi(p["RT_D"], p["RT_S"]), mode=True)
    if nl:
        xlt = xf + 0.6 * TL_OUT
        co([v.P(xlt, z) for z in zs_tl], v.x(xf + TL_OUT) + 3.0, v.y(zs_tl[0]) + 3.0, 1, 24,
           phi(p["TL_D"], p["TL_S"]), mode=True)
    # kích thước
    yd = v.y(-tl) - 5.0
    v.dimH((-L, 0.0), (px - bb / 2, 0.0), yd)
    v.dimH((px - bb / 2, 0.0), (px + bb / 2, 0.0), yd)
    v.dimH((px + bb / 2, 0.0), (0.0, 0.0), yd)
    xd = v.x(-L - ml) - 4.0
    v.dimV((-L, 0.0), (-L, hd), v.x(-L) - 3.5)
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
        mesh(c, g, co, 214.0, 246.0)
    with c.group("sec55", "Mặt cắt 5-5"):
        pier_section(c, g, co, 214.0, 165.0)
    tables.summary(c, g, 405.0, 98.0)
    note_at(c, 268.0, min(ybb, 125.0), ["- XEM GHI CHÚ CHUNG TẠI BẢN VẼ SỐ: " + str(g.p.get("CODE", "")),
                                         "- KÍCH THƯỚC GHI TRÊN BẢN VẼ TÍNH BẰNG mm."])
