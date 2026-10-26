"""Bố trí hình học, cốt thép và bảng thống kê thép của móng bản có dầm.

Toạ độ cục bộ (m): gốc tại tim móng, X theo cạnh L, Y theo cạnh B, z từ đáy bản móng lên.
2 dầm theo Y tại x = ±L1/2, 2 dầm theo X tại y = ±L2/2, cổ móng tại 4 giao điểm.
Quy tắc số thanh / chiều dài theo sheet "KL thep mong" của Excel mẫu; khối lượng tính từ đúng các thanh vẽ ra."""
from __future__ import annotations

import math

from . import model

KGM = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 18: 2.0, 20: 2.47,
       22: 2.98, 25: 3.85, 28: 4.83, 32: 6.31, 36: 7.99, 40: 9.86, 50: 15.42}
NPIER = model.NPIER
HOOK = 0.06          # móc đai, đai phụ (m)
CH_LEG = 0.1         # chân thanh chống (m)
ANCHOR = 0.5         # đoạn neo thép chủ cổ móng (m), cố định
TL_LEG, TL_W, TL_OUT = 0.35, 0.3, 0.15   # thang leo: chân ngàm vào cổ, bề rộng bậc, nhô ra khỏi mặt cổ
H_TL0 = 1.5          # thang leo bắt đầu từ cao độ +1.5 m so với mặt đất


def ceil_(x):
    return int(x) + 1 if x > int(x) + 1e-6 else int(x)


def xround(x):
    """ROUND của Excel (0.5 làm tròn lên)."""
    return int(math.floor(x + 0.5 + 1e-9))


def kg(d, tot):
    a = KGM.get(int(d + 0.5))
    return tot * (a if a else d * d / 162.0)


def lin(x0, x1, s):
    """Rải thép từ x0 tới x1 (đã trừ lớp bảo vệ), số thanh = ROUND((x1 - x0) / s) + 1 như Excel."""
    w = x1 - x0
    if w < -1e-9:
        return []
    n = max(2, xround(w / s) + 1) if w > 1e-6 else 1
    if n == 1:
        return [0.5 * (x0 + x1)]
    return [x0 + i * w / (n - 1) for i in range(n)]


def cells(x0, x1, s):
    """Vị trí giữa các ô chia đều (thanh chống), số ô = ceil(w / s)."""
    w = x1 - x0
    if w <= 1e-6:
        return []
    n = max(1, ceil_(w / s - 1e-6))
    return [x0 + (i + 0.5) * w / n for i in range(n)]


def stations(x0, x1, s):
    """Đai rải đều trên đoạn [x0, x1], 2 đầu có đai: 1 + ceil(w / s)."""
    w = x1 - x0
    if w <= 1e-6:
        return []
    n = 1 + max(1, ceil_(w / s - 1e-6))
    return [x0 + i * w / (n - 1) for i in range(n)]


class Geo:
    """Toàn bộ kích thước bố trí của 1 móng."""

    def __init__(self, p: dict):
        self.p = p
        self.layout()

    def g(self, k):
        return self.p[k]

    # ------------------------------------------------------------------
    def layout(self):
        p = self.p
        self.den = int(p["SCALE"] + 0.5)
        self.k = 1000.0 / self.den
        self.Lh, self.Bh = p["L"] / 2, p["B"] / 2
        self.dx, self.dy = p["L1"] / 2, p["L2"] / 2
        self.a, self.hd, self.hs = p["A"], p["HD"], p["HS"]
        self.c, self.e, self.bb = p["C"], p["E"], p["BB"]
        self.H = model.H(p)
        self.cov, self.covb = p["COVER"], p["COVER_B"]
        self.hasCushion = p["HC"] > 1e-6
        self.hasHole = self.c > 1e-6
        self.hasHaunch = self.e > 1e-6
        self.ds = p["RS_D"] / 1000.0
        self.dm = p["RD_D"] / 1000.0
        self.dt = p["RDT_D"] / 1000.0
        self.dg = p["RG_D"] / 1000.0
        # bề rộng ô bản ngoài (từ mặt dầm tới mép móng)
        self.D1 = self.Lh - self.dx - self.a / 2
        self.D2 = self.Bh - self.dy - self.a / 2
        self.slab_bars()
        self.rib_bars()

    def long_x(self):
        """True nếu cạnh dài theo X (L >= B): thép theo X nằm ngoài cùng ở cả lớp dưới và lớp trên."""
        return self.g("L") >= self.g("B")

    # ---- vùng bản móng ----------------------------------------------------
    def zones(self, half, d):
        """Các vùng rải thép bản theo 1 phương: (z0, z1, loại). half = nửa cạnh, d = tim dầm."""
        a, c = self.a, self.c
        out = [(-half, -d - a / 2, "out"), (d + a / 2, half, "out")]
        if self.hasHole:
            out += [(-d + a / 2, -c / 2, "in"), (c / 2, d - a / 2, "in")]
        else:
            out += [(-d + a / 2, d - a / 2, "in")]
        return sorted(out)

    def slab_bars(self):
        """Vị trí thép bản (m): xs1/xs2 = thanh theo Y (vị trí x), ys3/ys4 = thanh theo X (vị trí y)."""
        cov, c = self.cov, self.c
        s1, s2 = self.g("RS_S1") / 1000.0, self.g("RS_S2") / 1000.0
        self.xs1, self.ys3 = [], []
        for z0, z1, kd in self.zones(self.Lh, self.dx):
            self.xs1 += lin(z0 + cov, z1 - cov, s2 if kd == "out" else s1)
        for z0, z1, kd in self.zones(self.Bh, self.dy):
            self.ys3 += lin(z0 + cov, z1 - cov, s2 if kd == "out" else s1)
        self.xs1.sort()
        self.ys3.sort()
        self.xs2 = lin(-c / 2 + cov, c / 2 - cov, s1) if self.hasHole else []
        self.ys4 = lin(-c / 2 + cov, c / 2 - cov, s1) if self.hasHole else []
        # thanh chống
        sc1, sc2 = self.g("RCH_S1") / 1000.0, self.g("RCH_S2") / 1000.0

        def chair_axis(half, d):
            zs = self.zones(half, d)
            if self.hasHole:
                zs.append((-c / 2, c / 2, "in"))
            out = []
            for z0, z1, kd in zs:
                out += cells(z0 + cov, z1 - cov, sc2 if kd == "out" else sc1)
            return sorted(out)
        self.chx, self.chy = chair_axis(self.Lh, self.dx), chair_axis(self.Bh, self.dy)
        hh = c / 2 + cov
        self.chairs = [(x, y) for x in self.chx for y in self.chy
                       if not (self.hasHole and abs(x) < hh and abs(y) < hh)]
        # thép xiên góc lỗ
        n2 = 4 * len(self.xs2)
        self.n5 = n2 if n2 % 8 == 0 else (n2 // 8) * 8
        self.l5 = round(c * math.sqrt(2), 2) + 0.8 if self.hasHole else 0.0

    def slab_z(self):
        """Cao độ tâm thép bản: (z thanh Y lớp dưới, z thanh X lớp dưới, z thanh Y lớp trên, z thanh X lớp trên)."""
        d, cb, ct, hs = self.ds, self.covb, self.cov, self.hs
        if self.long_x():   # thanh theo X ngoài cùng
            return cb + 1.5 * d, cb + 0.5 * d, hs - ct - 1.5 * d, hs - ct - 0.5 * d
        return cb + 0.5 * d, cb + 1.5 * d, hs - ct - 0.5 * d, hs - ct - 1.5 * d

    def chair_body(self):
        return self.hs - self.cov - self.covb - 2 * self.ds

    # ---- dầm ------------------------------------------------------------
    def rib_bars(self):
        """Bố trí thép chủ dầm trên mặt cắt ngang dầm (u: ngang từ tim dầm, z: từ đáy).
        self.rows = [(z, [(u, full?), ...]), ...] cho cả mặt dưới và mặt trên."""
        a, cov, d, dt = self.a, self.cov, self.dm, self.dt
        n = int(round(self.g("RD_N")))
        self.n_full = n // 2 if n % 4 == 0 else n // 2 + 1
        self.n_full = min(n, self.n_full)
        self.n_cut = n - self.n_full
        gap = max(0.025, d)
        w_in = a - 2 * cov - 2 * dt
        m = max(2, int((w_in + gap + 1e-9) / (d + gap)))
        nrow = max(1, ceil_(n / m))
        per = [ceil_(n / nrow)] * nrow
        per[-1] = n - sum(per[:-1])
        self.rib_gap = gap
        um = w_in / 2 - d / 2
        rows_b, rows_t = [], []
        left = self.n_full
        for i, cnt in enumerate(per):
            us = [0.0] if cnt == 1 else [-um + j * 2 * um / (cnt - 1) for j in range(cnt)]
            fl = [False] * cnt
            if left >= cnt:
                fl = [True] * cnt
                left -= cnt
            else:   # thanh dài suốt đặt ở 2 đầu hàng, đối xứng
                order = sorted(range(cnt), key=lambda j: -abs(us[j]))
                for j in order[:left]:
                    fl[j] = True
                left = 0
            zb = self.covb + dt + d / 2 + i * (d + gap)
            zt = self.hd - cov - dt - d / 2 - i * (d + gap)
            rows_b.append((zb, list(zip(us, fl))))
            rows_t.append((zt, list(zip(us, fl))))
        self.rows_b, self.rows_t = rows_b, rows_t
        hh = self.hd - cov - self.covb
        self.n_gia = 1 if hh <= 1.0 + 1e-6 else 2 if hh <= 1.6 + 1e-6 else 3
        z0 = rows_b[-1][0] + d / 2
        z1 = rows_t[-1][0] - d / 2
        self.z_gia = [z0 + (i + 1) * (z1 - z0) / (self.n_gia + 1) for i in range(self.n_gia)]
        self.u_gia = w_in / 2 - self.dg / 2
        # đoạn cắt bớt mỗi đầu thanh ngắt = 1/2 khoảng từ mép dầm ngang tới mép móng (theo dầm đang cắt), làm tròn lên 100
        self.cut_y = math.ceil(self.D2 / 2 / 0.1 - 1e-6) * 0.1
        self.cut_x = math.ceil(self.D1 / 2 / 0.1 - 1e-6) * 0.1

    def rib_len(self, along_y):
        full = (self.g("B") if along_y else self.g("L")) - 2 * self.cov
        return full, max(0.0, full - 2 * (self.cut_y if along_y else self.cut_x))

    def has_tie2(self):
        """Thép chủ dầm 2 lớp -> thêm đai phụ ngang giữ lớp thứ 2 (mặt trên và mặt dưới)."""
        return len(self.rows_b) > 1

    def rib_segments(self, along_y):
        """Đoạn dầm rải đai (bỏ vùng giao dầm + vát nách), toạ độ dọc dầm."""
        half = self.Bh if along_y else self.Lh
        d = self.dy if along_y else self.dx
        w = self.a / 2 + self.e
        return [(-half + self.cov, -d - w), (-d + w, d - w), (d + w, half - self.cov)]

    def stirrups(self, along_y):
        s = self.g("RDT_S") / 1000.0
        out = []
        for a0, a1 in self.rib_segments(along_y):
            out += stations(a0, a1, s)
        return out

    def ties(self, along_y):
        s = self.g("RDP_S") / 1000.0
        out = []
        for a0, a1 in self.rib_segments(along_y):
            out += stations(a0, a1, s)
        return out

    def has_vtie(self):
        return self.a > 0.6 + 1e-6

    # ---- vát nách -------------------------------------------------------
    def l7(self):
        a, e, c = self.a, self.e, self.cov
        return math.sqrt(2) * (2 * a + e) - 2 * math.sqrt(2) * c - 2 * c

    def l8(self):
        return math.sqrt(2) * (self.a + self.e) - 2 * self.cov

    def n8(self):
        return max(1, int(math.floor((self.l8() + 2 * self.cov) / 0.3 - 1 + 1e-9)))

    def n9(self):
        return max(1, int(math.floor((self.hd - self.hs) / 0.2 + 1 + 1e-9)))

    def leg(self):
        return self.hd - 2 * self.cov

    # ---- cổ móng --------------------------------------------------------
    def hoop_zs(self):
        s = self.g("RT_S") / 1000.0
        z0 = self.H - self.cov
        n = 1 + max(1, ceil_((z0 - self.hd) / s - 1e-6))
        return [z0 - i * (z0 - self.hd) / (n - 1) for i in range(n)]

    def hoop_n(self, s):
        return 1 + max(1, ceil_((self.H - self.cov - self.hd) / s - 1e-6))

    def pier_vert(self):
        return self.H - self.cov - self.covb - 2 * self.ds

    def m_bars(self):
        return 1 + int(self.g("RC_N") / 4.0)

    def tie_idx(self):
        m = self.m_bars()
        w = 1000.0 * (self.g("BB") - 2 * self.g("COVER"))
        if m <= 2 or (w <= 400.0 and m <= 4):
            return []
        s = w / (m - 1)
        g = max(1, min(2, int(400.0 / s)))
        lst, i = [], 0
        while i <= (m - 1) / 2.0:
            lst.append(i)
            i += g
        res = []
        for j in lst:
            if j not in res:
                res.append(j)
            if (m - 1 - j) not in res:
                res.append(m - 1 - j)
        res.sort()
        extra, cur = [], res[0]
        for nx in res[1:]:
            while nx - cur > g:
                cur += g
                extra.append(cur)
            cur = nx
        res = sorted(set(res + extra))
        return sorted({j for j in res if 0 < j < m - 1})

    def tie_plan(self):
        ti = self.tie_idx()
        m = self.m_bars()
        runs, cur = [], []
        for j in ti:
            if cur and j == cur[-1] + 1:
                cur.append(j)
            else:
                if cur:
                    runs.append(cur)
                cur = [j]
        if cur:
            runs.append(cur)
        grp, st = None, []
        for run in runs:
            if grp is None and len(run) >= 2 and (m - 1 - run[0]) in run:
                c = len(run) if len(run) <= 3 else (2 if len(run) % 2 == 0 else 3)
                off = (len(run) - c) // 2
                grp = run[off:off + c]
                st += [j for j in run if j not in grp]
            else:
                st += run
        return grp, sorted(st)

    def oct_dim(self):
        grp = self.tie_plan()[0]
        m = self.m_bars()
        kk = 40.0
        r = max(0.35, 0.5 * self.g("RC_D") / 1000.0 * kk)
        hb = kk * (self.g("BB") / 2 - self.g("COVER")) - 0.2 - r
        rt = r + 0.12
        s = 2 * hb / (m - 1)
        return ((max(grp) - (m - 1) / 2.0) * s + 0.41421356 * rt) / kk, (hb + rt) / kk

    def n_ladder(self):
        h2 = self.g("H2")
        if h2 <= H_TL0 + 1e-6:
            return 0
        return xround((h2 - H_TL0 - self.cov) / (self.g("TL_S") / 1000.0)) + 1

    def ladder_piers(self):
        """2 trụ chéo nhau có thang leo, bậc ở mặt cổ móng quay vào tim theo X: (sx, sy)."""
        return [(1, -1), (-1, 1)]

    # ---- khối lượng thép ------------------------------------------------
    def calc_kl(self):
        """Bảng thống kê thép (cho 01 móng). Mỗi dòng: dict(pos, dia, len, qty, tot, kg, dims, name)."""
        g = self.g
        cov = self.cov
        rows = []

        def R(pos, dia, ln, n, dims, name):
            if n <= 0 or ln <= 1e-6:
                return
            rows.append(dict(pos=pos, dia=dia, len=1000 * ln, qty=str(n), tot=n * ln, kg=kg(dia, n * ln),
                             dims=dims, name=name, n=n))
        ds = g("RS_D")
        L, B, c = g("L"), g("B"), self.c
        # 1-4: thép bản móng (2 lớp)
        R(1, ds, B - 2 * cov, 2 * len(self.xs1), [1000 * (B - 2 * cov)], "Thép bản móng theo Y")
        l2 = B / 2 - c / 2 - 2 * cov
        R(2, ds, l2, 4 * len(self.xs2), [1000 * l2], "Thép bản theo Y, ngắt tại lỗ")
        R(3, ds, L - 2 * cov, 2 * len(self.ys3), [1000 * (L - 2 * cov)], "Thép bản móng theo X")
        l4 = L / 2 - c / 2 - 2 * cov
        R(4, ds, l4, 4 * len(self.ys4), [1000 * l4], "Thép bản theo X, ngắt tại lỗ")
        # 5: thép xiên góc lỗ
        if self.hasHole:
            R(5, ds, self.l5, self.n5, [1000 * self.l5], "Thép xiên góc lỗ")
        # 6: thanh chống
        bd = self.chair_body()
        R(6, g("RCH_D"), bd + 2 * CH_LEG, len(self.chairs), [1000 * CH_LEG, 1000 * CH_LEG, 1000 * bd], "Thanh chống")
        # 7-9: vát nách tại 4 chỗ giao dầm
        if self.hasHaunch:
            lg = self.leg()
            l7, l8 = self.l7(), self.l8()
            R(7, g("RDT_D"), l7 + 2 * lg, 4 * 4, [1000 * lg, 1000 * lg, 1000 * l7], "Thép vát nách (dài)")
            R(8, g("RDT_D"), l8 + 2 * lg, 2 * self.n8() * 4, [1000 * lg, 1000 * lg, 1000 * l8], "Thép vát nách (ngắn)")
            R(9, g("RDT_D"), 4 * l8 + 2 * HOOK, self.n9() * 4, [1000 * HOOK, 1000 * l8], "Đai vuông vát nách")
        # 10-15: thép chủ, thép giá dầm
        dm = g("RD_D")
        for along_y, p0 in ((True, 10), (False, 13)):
            full, cut = self.rib_len(along_y)
            nm = "theo Y" if along_y else "theo X"
            R(p0, dm, full, self.n_full * 2 * 2, [1000 * full], f"Thép chủ dầm {nm} (dài suốt)")
            R(p0 + 1, dm, cut, self.n_cut * 2 * 2, [1000 * cut], f"Thép chủ dầm {nm} (ngắt)")
            R(p0 + 2, g("RG_D"), full, self.n_gia * 2 * 2, [1000 * full], f"Thép giá dầm {nm}")
        # 16-18: đai dầm, đai phụ
        w, hh = self.a - 2 * cov, self.hd - 2 * cov
        ns = 2 * (len(self.stirrups(True)) + len(self.stirrups(False)))
        R(16, g("RDT_D"), 2 * w + 2 * hh + 2 * HOOK, ns, [1000 * HOOK, 1000 * w, 1000 * hh], "Đai dầm")
        nt = 2 * (len(self.ties(True)) + len(self.ties(False)))
        R(17, g("RDP_D"), w + 2 * HOOK, nt * self.n_gia, [1000 * HOOK, 1000 * w, 1000 * HOOK], "Đai phụ ngang dầm")
        if self.has_tie2():
            R(26, g("RDP_D"), w + 2 * HOOK, nt * 2, [1000 * HOOK, 1000 * w, 1000 * HOOK], "Đai phụ giữ lớp thép 2 dầm")
        if self.has_vtie():
            R(18, g("RDP_D"), hh + 2 * HOOK, nt, [1000 * HOOK, 1000 * hh, 1000 * HOOK], "Đai phụ đứng dầm")
        # 19-23: cổ móng
        vert = self.pier_vert()
        R(19, g("RC_D"), vert + ANCHOR, NPIER * int(g("RC_N")), [1000 * ANCHOR, 1000 * vert], "Thép chủ cổ móng")
        rows[-1]["qty"] = f"{int(g('RC_N'))}x{NPIER}"
        side = self.bb - 2 * cov
        n20 = self.hoop_n(g("RT_S") / 1000.0)
        R(20, g("RT_D"), 4 * side + 2 * HOOK, n20 * NPIER, [1000 * HOOK, 1000 * side], "Đai cổ móng")
        rows[-1]["qty"] = f"{n20}x{NPIER}"
        grp, st = self.tie_plan()
        n9 = self.hoop_n(g("RP_S") / 1000.0)
        if st:
            R(21, g("RP_D"), side + 2 * HOOK, n9 * 2 * len(st) * NPIER, [1000 * HOOK, 1000 * side, 1000 * HOOK],
              "Đai phụ thẳng cổ móng")
            rows[-1]["qty"] = f"{n9 * 2 * len(st)}x{NPIER}"
        if grp:
            a_, f_ = self.oct_dim()
            ln = 8 * a_ + 4 * math.sqrt(2) * (f_ - a_) + 2 * HOOK
            R(22, g("RP_D"), ln, n9 * NPIER, [2000 * a_, 1414.2136 * (f_ - a_), 1000 * HOOK], "Đai bát giác cổ móng")
            rows[-1]["qty"] = f"{n9}x{NPIER}"
        hh2 = self.bb / 2 - cov
        nn = 1 + ceil_(2 * hh2 / (g("RL_S") / 1000.0) - 1e-6)
        R(23, g("RL_D"), 2 * hh2, int(g("RL_N")) * 2 * nn * NPIER, [2000 * hh2], "Lưới thép đầu trụ")
        # 24: thang leo
        nl = self.n_ladder()
        if nl:
            R(24, g("TL_D"), 2 * TL_LEG + TL_W, nl * len(self.ladder_piers()),
              [1000 * TL_LEG, 1000 * TL_LEG, 1000 * TL_W], "Thang leo")
        cls = {}
        for r in rows:
            a = cls.setdefault(r["dia"], [0.0, 0.0])
            a[0] += r["tot"]
            a[1] += r["kg"]
        self.kl = rows
        self.klc = sorted((d, v[0], v[1]) for d, v in cls.items())
        self.seq = {r["pos"]: i for i, r in enumerate(rows, 1)}
        return rows

    def sq(self, num) -> str:
        """Số vị trí hiển thị liên tục 1..n."""
        try:
            return str(self.seq.get(int(num), num))
        except (ValueError, AttributeError):
            return str(num)
