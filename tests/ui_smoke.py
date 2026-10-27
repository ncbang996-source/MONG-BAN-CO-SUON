"""Kiểm thử giao diện (chạy trên Windows CI): mở app, dựng bản vẽ mẫu, mở tab 3D, xoay / phóng / dịch,
chụp ảnh cửa sổ vào thư mục shots/."""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["APPDATA"] = tempfile.mkdtemp()          # không đụng cấu hình thật

from PIL import ImageGrab  # noqa: E402

import app as A  # noqa: E402
from mongban import cad  # noqa: E402

OUT = os.path.join(ROOT, "shots")
os.makedirs(OUT, exist_ok=True)
cad.init_fonts()
w = A.App()
w.geometry("1600x960+0+0")
w.update()


def pump(sec):
    t = time.time()
    while time.time() - t < sec:
        w.update()
        time.sleep(0.02)


def shot(name):
    pump(0.5)
    x, y = w.winfo_rootx(), w.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height())).save(os.path.join(OUT, name))


w.read_excel(os.path.join(ROOT, "samples", "D122-42_MB4-10x12-2.5.xlsm"))
t0 = time.time()
while (w.busy or not w.pages) and time.time() - t0 < 120:
    pump(0.2)
assert w.pages, "không dựng được bản vẽ"
shot("1_ban_in.png")
w.nb.select(1)
pump(1.0)
v = w.v3d
assert v.p is not None and not v.stale, "tab 3D chưa dựng"
shot("2_3d_toan_mong.png")
cv = v.cv
cv.event_generate("<ButtonPress-1>", x=400, y=300)
for i in range(10):
    cv.event_generate("<B1-Motion>", x=400 + 12 * i, y=300 + 3 * i)
    w.update()
cv.event_generate("<ButtonRelease-1>", x=508, y=327)
shot("3_3d_xoay.png")
v.v_q.set(True)
v._scope()
shot("4_3d_cat_1_4.png")
for _ in range(6):
    v.zoom_at(1.25, cv.winfo_width() * 0.45, cv.winfo_height() * 0.45)
shot("5_3d_phong_to.png")
for key in ("bt", "slab"):
    v.v_lay[key].set(False)
v.refresh()
shot("6_3d_tat_be_tong_thep_ban.png")
w.destroy()
print("OK - giao dien 3D")
