"""Mô hình 3D diễn hoạ cốt thép (bê tông trong suốt + thép màu), vẽ bằng Pillow, không cần OpenGL."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from . import model

COL = {
    "lot": (150, 150, 140), "bt": (176, 182, 96), "edge": (80, 84, 40),
    "slab_y": (200, 30, 40), "slab_x": (90, 40, 200), "slab_h": (230, 120, 0),
    "rib": (150, 0, 20), "dai": (40, 80, 230), "gia": (120, 60, 160),
    "pier": (220, 90, 20), "hoop": (30, 110, 210), "bg": (255, 255, 255),
    "tie": (0, 150, 200), "chair": (90, 90, 90), "haunch": (0, 140, 90), "mesh": (60, 60, 200),
    "bolt": (70, 70, 70), "ladder": (110, 110, 110),
}
LAYERS = ("bt", "slab", "rib", "dai", "pier")


def box(x0, x1, y0, y1, z0, z1):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return [[p[i] for i in q] for q in f]


def prism(pts, z0, z1):
    """Lăng trụ đáy đa giác pts (x, y)."""
    bot = [(x, y, z0) for x, y in pts]
    top = [(x, y, z1) for x, y in pts]
    out = [bot, top]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        out.append([bot[i], bot[j], top[j], top[i]])
    return out


class Scene:
    """Danh sách mặt bê tông và đoạn thép (m, gốc tại tim móng, z = 0 ở đáy bản)."""

    def __init__(self, g, quarter=False):
        self.g = g
        self.lim = (-0.0, -0.0) if quarter else (-1e9, -1e9)   # cắt 1/4: chỉ giữ x >= 0, y >= 0
        self.faces = []      # (layer, color, alpha, [pts])
        self.lines = []      # (layer, color, width_m, p0, p1)
        self.build()

    def B(self, lay, col, al, x0, x1, y0, y1, z0, z1, only=None):
        cut = (5,) if x0 < self.lim[0] else ()      # mặt bị cắt 1/4 luôn hiện
        cut += (2,) if y0 < self.lim[1] else ()
        x0, y0 = max(x0, self.lim[0]), max(y0, self.lim[1])
        if x1 - x0 < 1e-6 or y1 - y0 < 1e-6:
            return
        fs = box(x0, x1, y0, y1, z0, z1)
        self.F(lay, col, al, fs if only is None else [fs[i] for i in set(only + cut)])

    def F(self, lay, col, al, faces):
        for f in faces:
            if all(p[0] >= self.lim[0] - 1e-9 and p[1] >= self.lim[1] - 1e-9 for p in f):
                self.faces.append((lay, col, al, f))

    def L(self, lay, col, d, pts, closed=False):
        n = len(pts)
        for i in range(n if closed else n - 1):
            p0, p1 = np.array(pts[i], float), np.array(pts[(i + 1) % n], float)
            t0, t1 = 0.0, 1.0
            for ax in (0, 1):                 # xén đoạn theo mặt cắt 1/4
                a, b, m = p0[ax], p1[ax], self.lim[ax]
                if a < m and b < m:
                    t0 = 2.0
                elif a < m:
                    t0 = max(t0, (m - a) / (b - a))
                elif b < m:
                    t1 = min(t1, (m - a) / (b - a))
            if t1 - t0 > 1e-6:
                self.lines.append((lay, col, d, tuple(p0 + t0 * (p1 - p0)), tuple(p0 + t1 * (p1 - p0))))

    def build(self):
        g = self.g
        g.slab_bars()
        g.rib_bars()
        L, B, a, e, hs, hd = g.Lh, g.Bh, g.a, g.e, g.hs, g.hd
        dx, dy, c, bb, H = g.dx, g.dy, g.c, g.bb, g.H
        ml = model.ML
        # bê tông lót, bản, dầm, vát nách, cổ móng
        bt, al = COL["bt"], 0.16
        self.B("bt", COL["lot"], 0.30, -L - ml, L + ml, -B - ml, B + ml, -model.TL, 0.0, only=(1,))
        if g.hasHole:
            h = c / 2
            for bx in ((-L, L, h, B), (-L, L, -B, -h), (-L, -h, -h, h), (h, L, -h, h)):
                self.B("bt", bt, al, *bx, 0, hs)
        else:
            self.B("bt", bt, al, -L, L, -B, B, 0, hs)
        xs = [-L, -dx - a / 2, -dx + a / 2, dx - a / 2, dx + a / 2, L]
        for s in (-1, 1):
            self.B("bt", bt, al, s * dx - a / 2, s * dx + a / 2, -B, B, hs, hd)
            for i in (0, 2, 4):              # dầm theo X chia đoạn giữa các dầm theo Y (không chồng nét)
                self.B("bt", bt, al, xs[i], xs[i + 1], s * dy - a / 2, s * dy + a / 2, hs, hd,
                       only=(1, 2, 4) + ((5,) if i == 0 else ()) + ((3,) if i == 4 else ()))
        if g.hasHaunch:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    for qx in (-1, 1):
                        for qy in (-1, 1):
                            x0, y0 = sx * dx + qx * a / 2, sy * dy + qy * a / 2
                            tri = [(x0, y0), (x0 + qx * e, y0), (x0, y0 + qy * e)]
                            self.F("bt", bt, al, prism(tri, hs, hd))
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = sx * dx, sy * dy
                self.B("bt", bt, al, x - bb / 2, x + bb / 2, y - bb / 2, y + bb / 2, hd, H)
        # thép bản 2 lớp
        cov = g.cov
        zy_b, zx_b, zy_t, zx_t = g.slab_z()
        ds = g.ds
        hh = c / 2 + cov
        for zy in (zy_b, zy_t):
            for x in g.xs1:
                self.L("slab", COL["slab_y"], ds, [(x, -B + cov, zy), (x, B - cov, zy)])
            for x in g.xs2:
                for y0, y1 in ((-B + cov, -hh), (hh, B - cov)):
                    self.L("slab", COL["slab_y"], ds, [(x, y0, zy), (x, y1, zy)])
        for zx in (zx_b, zx_t):
            for y in g.ys3:
                self.L("slab", COL["slab_x"], ds, [(-L + cov, y, zx), (L - cov, y, zx)])
            for y in g.ys4:
                for x0, x1 in ((-L + cov, -hh), (hh, L - cov)):
                    self.L("slab", COL["slab_x"], ds, [(x0, y, zx), (x1, y, zx)])
        if g.hasHole:           # thép xiên góc lỗ
            l5 = g.l5 / 2
            for sx in (-1, 1):
                for sy in (-1, 1):
                    cx, cy = sx * (hh + 0.1), sy * (hh + 0.1)
                    u = (sx * 0.7071, -sy * 0.7071)
                    for z in (zy_b, zy_t):
                        self.L("slab", COL["slab_h"], ds,
                               [(cx - u[0] * l5, cy - u[1] * l5, z), (cx + u[0] * l5, cy + u[1] * l5, z)])
        # thép dầm
        dm, dt = g.dm, g.dt
        for along_y in (True, False):
            full, cut = g.rib_len(along_y)
            for s in (-1, 1):
                t = s * (dx if along_y else dy)
                rows_b = g.rows_bot(along_y)
                for z, row in rows_b + g.rows_t:
                    for u, fl in row:
                        ln = (full if fl else cut) / 2
                        p0 = (t + u, -ln, z) if along_y else (-ln, t + u, z)
                        p1 = (t + u, ln, z) if along_y else (ln, t + u, z)
                        self.L("rib", COL["rib"], dm, [p0, p1])
                for z in g.z_gia:
                    for u in (-g.u_gia, g.u_gia):
                        ln = full / 2
                        p0 = (t + u, -ln, z) if along_y else (-ln, t + u, z)
                        p1 = (t + u, ln, z) if along_y else (ln, t + u, z)
                        self.L("rib", COL["gia"], g.dg, [p0, p1])
                # đai dầm, đai phụ ngang (mức thép giá + giữ lớp 2), đai phụ đứng
                uo = a / 2 - cov - dt / 2
                zb = rows_b[0][0] - dm / 2 - dt / 2
                zt = g.rows_t[0][0] + dm / 2 + dt / 2
                P = (lambda st, u, z: (t + u, st, z)) if along_y else (lambda st, u, z: (st, t + u, z))
                for st in g.stirrups(along_y):
                    self.L("dai", COL["dai"], dt, [P(st, u, z) for u, z in
                                                   ((-uo, zb), (uo, zb), (uo, zt), (-uo, zt))], True)
                dp = g.g("RDP_D") / 1000.0
                for st in g.ties(along_y):
                    st += 0.03                           # lệch khỏi đai chính cho dễ nhìn
                    for z in list(g.z_gia):
                        self.L("dai", COL["tie"], dp, [P(st, -uo, z), P(st, uo, z)])
                    if g.has_vtie():
                        self.L("dai", COL["tie"], dp, [P(st, 0.0, zb), P(st, 0.0, zt)])
                for st in g.ties2(along_y):              # giữ lớp 2: chỉ trong đoạn có thép lớp 2
                    st += 0.03
                    for z in g.z_tie2(along_y):
                        self.L("dai", COL["tie"], dp, [P(st, -uo, z), P(st, uo, z)])
        # thanh chống (6): thân đứng giữa 2 lớp thép bản, 2 chân ngang
        dch = g.g("RCH_D") / 1000.0
        from .geom import CH_LEG, ANCHOR, TL_LEG, TL_W, TL_OUT
        z0c = g.covb + ds                  # đỡ thanh ngoài cùng lớp dưới / lớp trên
        z1c = z0c + g.chair_body()
        for x, y in g.chairs:
            self.L("slab", COL["chair"], dch, [(x + CH_LEG, y, z0c), (x, y, z0c), (x, y, z1c), (x + CH_LEG, y, z1c)])
        # vát nách (7, 8, 9) tại 4 chỗ giao dầm
        if g.hasHaunch:
            r2 = 1 / math.sqrt(2)
            l7, l8, d7 = g.l7(), g.l8(), (a + e) / 2 - cov
            z7 = hd - cov
            z8 = z7 - dt - 0.02
            zs9 = [z8 - 0.03 - i * 0.2 for i in range(g.n9())]
            n8 = g.n8()
            ts = [-l8 / 2 + (i + 1) * l8 / (n8 + 1) for i in range(n8)]
            for sx in (-1, 1):
                for sy in (-1, 1):
                    X, Y = sx * dx, sy * dy
                    for qx in (-1, 1):
                        for qy in (-1, 1):
                            mx, my = X + qx * d7, Y + qy * d7
                            ux, uy = -qx * r2 * l7 / 2, qy * r2 * l7 / 2
                            self.L("rib", COL["haunch"], dt, [(mx - ux, my - uy, cov), (mx - ux, my - uy, z7),
                                                              (mx + ux, my + uy, z7), (mx + ux, my + uy, cov)])
                    for (nx, ny), (ux, uy) in (((r2, r2), (-r2, r2)), ((r2, -r2), (r2, r2))):
                        for tt in ts:
                            mx, my = X + nx * tt, Y + ny * tt
                            ex, ey = ux * l8 / 2, uy * l8 / 2
                            self.L("rib", COL["haunch"], dt, [(mx - ex, my - ey, cov), (mx - ex, my - ey, z8),
                                                              (mx + ex, my + ey, z8), (mx + ex, my + ey, cov)])
                    h8 = l8 / 2
                    sq = [(X + r2 * (p_ + q_) * h8, Y + r2 * (p_ - q_) * h8) for p_, q_ in
                          ((1, 1), (1, -1), (-1, -1), (-1, 1))]
                    for z in zs9:
                        self.L("rib", COL["haunch"], dt, [(x_, y_, z) for x_, y_ in sq], True)
        # cổ móng: thép chủ (neo chân bẻ ra ngoài), đai, lưới đầu trụ, bu lông, thang leo
        dc = g.g("RC_D") / 1000.0
        dh = g.g("RT_D") / 1000.0
        w = bb / 2 - cov - dc / 2
        m = g.m_bars()
        us = [-w + i * 2 * w / (m - 1) for i in range(m)]
        ring = [(u, -w) for u in us] + [(w, u) for u in us[1:]] + \
               [(u, w) for u in reversed(us[:-1])] + [(-w, u) for u in reversed(us[1:-1])]
        z0, z1 = g.covb + 2 * ds, H - cov
        dl, sl = g.g("RL_D") / 1000.0, g.g("RL_S") / 1000.0
        nd = max(1, math.ceil(2 * w / sl - 1e-6))
        db = model_bolt_d(g.p)
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = sx * dx, sy * dy
                for u, v in ring:
                    if abs(u) >= abs(v) - 1e-9:
                        ax = (math.copysign(ANCHOR, u), 0.0)
                    else:
                        ax = (0.0, math.copysign(ANCHOR, v))
                    self.L("pier", COL["pier"], dc, [(x + u, y + v, z1), (x + u, y + v, z0),
                                                     (x + u + ax[0], y + v + ax[1], z0)])
                wh = w + dc / 2 + dh / 2
                for z in g.hoop_zs():
                    self.L("pier", COL["hoop"], dh,
                           [(x - wh, y - wh, z), (x + wh, y - wh, z), (x + wh, y + wh, z), (x - wh, y + wh, z)], True)
                for il in range(int(g.g("RL_N"))):
                    z = z1 - 0.02 - il * sl
                    for j in range(nd + 1):
                        o = -w + j * 2 * w / nd
                        self.L("pier", COL["mesh"], dl, [(x + o, y - w, z), (x + o, y + w, z)])
                        self.L("pier", COL["mesh"], dl, [(x - w, y + o, z - dl), (x + w, y + o, z - dl)])
                ob = 0.47 * bb / 2
                for bx in (-1, 1):
                    for by in (-1, 1):
                        px, py = x + bx * ob, y + by * ob
                        # phần nhô lên khỏi đỉnh cổ (chiều dài neo không có trong số liệu -> không vẽ phần chôn)
                        self.L("pier", COL["bolt"], db * 0.8, [(px, py, H), (px, py, H + 0.25)])
                        hn = 0.9 * db
                        for zn in (H + 0.06, H + 0.14):
                            self.L("pier", COL["bolt"], 0.012, [(px - hn, py - hn, zn), (px + hn, py - hn, zn),
                                                               (px + hn, py + hn, zn), (px - hn, py + hn, zn)], True)
        nl = g.n_ladder()
        if nl:
            dtl = g.g("TL_D") / 1000.0
            for sx, sy in g.ladder_piers():
                xf, sg = sx * dx - sx * bb / 2, -sx
                y = sy * dy
                for i in range(nl):
                    z = H - cov - i * g.g("TL_S") / 1000.0
                    self.L("pier", COL["ladder"], dtl, [(xf - sg * TL_LEG, y - TL_W / 2, z), (xf + sg * TL_OUT, y - TL_W / 2, z),
                                                        (xf + sg * TL_OUT, y + TL_W / 2, z), (xf - sg * TL_LEG, y + TL_W / 2, z)])

    def bounds(self):
        pts = np.array([p for f in self.faces for p in f[3]] or [(0, 0, 0)])
        return pts.min(0), pts.max(0)


def model_bolt_d(p):
    """Đường kính bu lông (m) đọc từ chữ BLN, vd 'BLN-M56' -> 0.056."""
    import re
    m_ = re.search(r"M\s*(\d+)", str(p.get("BLN", "")))
    return (int(m_.group(1)) if m_ else 36) / 1000.0


def axes2d(yaw, pitch):
    """Hướng 2D (phải, lên) của 3 trục X, Y, Z trên màn hình (để vẽ biểu tượng trục)."""
    R = rot(yaw, pitch)
    return [(R[0, i], R[1, i]) for i in range(3)]


def rot(yaw, pitch):
    cy_, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    return np.array([[cy_, -sy_, 0.0], [sy_ * sp, cy_ * sp, cp], [-sy_ * cp, -cy_ * cp, sp]])   # hàng: phải, lên, về phía người xem


def render(scene: Scene, w=1200, h=800, yaw=-35.0, pitch=28.0, zoom=1.0, layers=LAYERS, ss=2,
           pan=(0.0, 0.0), fast=False, center=None) -> Image.Image:
    """Chiếu song song (trục đo), mặt bê tông trong suốt vẽ xa -> gần, sau đó thép xa -> gần.
    Tỷ lệ theo mặt cầu bao mô hình nên không nhảy khi xoay. fast: bản nháp khi đang kéo chuột."""
    if fast:
        ss = 1
    W, Hh = w * ss, h * ss
    R = rot(yaw, pitch)
    lo, hi = scene.bounds()
    ctr = (lo + hi) / 2
    rad = max(1e-3, 0.5 * float(np.linalg.norm(hi - lo)))
    k = zoom * 1.3 * min(W, Hh) / (2 * rad)
    c2 = R @ (ctr if center is None else np.asarray(center, float))
    ox = W / 2 - k * c2[0] + pan[0] * ss
    oy = Hh / 2 + k * c2[1] + pan[1] * ss

    def proj(pts):
        return np.asarray(pts, float) @ R.T

    def scr(q):
        return [(ox + k * a, oy - k * b) for a, b in q[:, :2]]

    img = Image.new("RGBA", (W, Hh), COL["bg"] + (255,))
    if "bt" in layers:
        fs = []
        for lay, col, al, f in scene.faces:
            qq = proj(f)
            fs.append((qq[:, 2].mean(), col, al, scr(qq)))
        fs.sort(key=lambda t: t[0])
        for _, col, al, pts in fs:          # ghép từng mặt trong khung bao của nó (nhanh hơn ghép cả ảnh)
            x0 = max(0, int(min(p[0] for p in pts)) - 1)
            y0 = max(0, int(min(p[1] for p in pts)) - 1)
            x1 = min(W, int(max(p[0] for p in pts)) + 2)
            y1 = min(Hh, int(max(p[1] for p in pts)) + 2)
            if x1 <= x0 or y1 <= y0:
                continue
            tile = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
            ImageDraw.Draw(tile).polygon([(a - x0, b - y0) for a, b in pts], fill=col + (int(255 * al),))
            img.alpha_composite(tile, (x0, y0))
        dr = ImageDraw.Draw(img, "RGBA")
        for _, col, al, pts in fs:
            dr.line(pts + [pts[0]], fill=COL["edge"] + (120,), width=max(1, ss))
    dr = ImageDraw.Draw(img)
    ls = [t for t in scene.lines if t[0] in layers]
    if ls:
        p0 = proj([t[3] for t in ls])
        p1 = proj([t[4] for t in ls])
        dep = (p0[:, 2] + p1[:, 2]) / 2
        s0, s1 = scr(p0), scr(p1)
        for i in np.argsort(dep):
            col, d = ls[i][1], ls[i][2]
            wd = max(1, int(round(k * d * 1.1)))
            dr.line([s0[i], s1[i]], fill=col + (255,), width=wd)
    img = img.convert("RGB")
    return img if ss == 1 else img.resize((w, h), Image.LANCZOS)
