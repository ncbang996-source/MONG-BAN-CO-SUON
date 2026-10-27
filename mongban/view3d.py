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
                for z, row in g.rows_b + g.rows_t:
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
                # đai
                uo = a / 2 - cov - dt / 2
                zb = g.rows_b[0][0] - dm / 2 - dt / 2
                zt = g.rows_t[0][0] + dm / 2 + dt / 2
                for st in g.stirrups(along_y):
                    q = [(-uo, zb), (uo, zb), (uo, zt), (-uo, zt)]
                    pts = [(t + u, st, z) if along_y else (st, t + u, z) for u, z in q]
                    self.L("dai", COL["dai"], dt, pts, True)
        # cổ móng
        dc = g.g("RC_D") / 1000.0
        dh = g.g("RT_D") / 1000.0
        w = bb / 2 - cov - dh - dc / 2
        m = g.m_bars()
        us = [-w + i * 2 * w / (m - 1) for i in range(m)]
        ring = [(u, -w) for u in us] + [(w, u) for u in us[1:]] + \
               [(u, w) for u in reversed(us[:-1])] + [(-w, u) for u in reversed(us[1:-1])]
        z0, z1 = g.covb + 2 * ds, H - cov
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = sx * dx, sy * dy
                for u, v in ring:
                    self.L("pier", COL["pier"], dc, [(x + u, y + v, z0), (x + u, y + v, z1)])
                wh = w + dc / 2 + dh / 2
                for z in g.hoop_zs():
                    self.L("pier", COL["hoop"], dh,
                           [(x - wh, y - wh, z), (x + wh, y - wh, z), (x + wh, y + wh, z), (x - wh, y + wh, z)], True)


def render(scene: Scene, w=1200, h=800, yaw=-35.0, pitch=28.0, zoom=1.0, layers=LAYERS, ss=2,
           pan=(0.0, 0.0)) -> Image.Image:
    """Chiếu trục đo (orthographic), vẽ mặt bê tông trong suốt theo thứ tự xa -> gần rồi đến thép."""
    W, Hh = w * ss, h * ss
    cy_, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    R = np.array([[cy_, -sy_, 0.0], [sy_ * sp, cy_ * sp, cp], [-sy_ * cp, -cy_ * cp, sp]])   # hàng: phải, lên, sâu

    def proj(pts):
        q = np.asarray(pts, float) @ R.T
        return q

    allp = np.array([p for f in scene.faces for p in f[3]])
    q = proj(allp)
    lo, hi = q.min(0), q.max(0)
    k = zoom * 0.9 * min(W / (hi[0] - lo[0]), Hh / (hi[1] - lo[1]))
    ox = W / 2 - k * (lo[0] + hi[0]) / 2 + pan[0] * ss
    oy = Hh / 2 + k * (lo[1] + hi[1]) / 2 + pan[1] * ss

    def scr(q):
        return [(ox + k * a, oy - k * b) for a, b in q[:, :2]]

    img = Image.new("RGBA", (W, Hh), COL["bg"] + (255,))
    if "bt" in layers:
        fs = []
        for lay, col, al, f in scene.faces:
            qq = proj(f)
            fs.append((qq[:, 2].mean(), col, al, scr(qq)))
        fs.sort(key=lambda t: t[0])
        ov = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
        for _, col, al, pts in fs:
            layer = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(pts, fill=col + (int(255 * al),))
            ov = Image.alpha_composite(ov, layer)
        img = Image.alpha_composite(img, ov)
        dr = ImageDraw.Draw(img)
        for _, col, al, pts in fs:
            dr.line(pts + [pts[0]], fill=COL["edge"] + (110,), width=max(1, ss))
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
    return img.convert("RGB").resize((w, h), Image.LANCZOS)
