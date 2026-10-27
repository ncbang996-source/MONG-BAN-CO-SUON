"""Kiểm thử giao diện (chạy trên Windows CI): mở app, dựng bản vẽ mẫu, mở tab 3D, xoay / phóng / dịch,
chụp ảnh cửa sổ vào thư mục shots/."""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["APPDATA"] = tempfile.mkdtemp()          # không đụng cấu hình thật
OUT = os.path.join(ROOT, "shots")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "log.txt"), "w", encoding="utf-8")
sys.stderr = LOG                                      # log lỗi tải cùng ảnh (artifact)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")




def log(*a):
    print(*a)
    print(*a, file=LOG, flush=True)


def main():
    """Chạy các bước trong mainloop (luồng dựng bản vẽ cần mainloop để gọi after())."""
    from PIL import ImageGrab

    import app as A
    from mongban import cad
    cad.init_fonts()
    w = A.App()
    w.geometry("1600x960+0+0")
    err = []

    def shot(name):
        w.update()
        x, y = w.winfo_rootx(), w.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height())).save(os.path.join(OUT, name))

    def steps():
        w.read_excel(os.path.join(ROOT, "samples", "D122-42_MB4-10x12-2.5.xlsm"))
        t0 = time.time()
        while (w.busy or not w.pages) and time.time() - t0 < 120:
            yield 0.3
        assert w.pages, "khong dung duoc ban ve"
        yield 0.5
        shot("1_ban_in.png")
        w.nb.select(1)
        yield 1.0
        v = w.v3d
        assert v.p is not None and not v.stale, "tab 3D chua dung"
        shot("2_3d_toan_mong.png")
        cv = v.cv
        cv.event_generate("<ButtonPress-1>", x=400, y=300)
        for i in range(10):
            cv.event_generate("<B1-Motion>", x=400 + 12 * i, y=300 + 3 * i)
            yield 0.05
        cv.event_generate("<ButtonRelease-1>", x=508, y=327)
        yield 0.5
        shot("3_3d_xoay.png")
        v.v_q.set(True)
        v._scope()
        yield 0.5
        shot("4_3d_cat_1_4.png")
        for _ in range(6):
            v.zoom_at(1.25, cv.winfo_width() * 0.45, cv.winfo_height() * 0.45)
        yield 0.5
        shot("5_3d_phong_to.png")
        for key in ("bt", "slab"):
            v.v_lay[key].set(False)
        v.refresh()
        yield 0.5
        shot("6_3d_tat_be_tong_thep_ban.png")

    it = steps()

    def tick():
        try:
            dt = next(it)
        except StopIteration:
            w.destroy()
            return
        except BaseException:
            import traceback
            err.append(traceback.format_exc())
            w.destroy()
            return
        w.after(int(dt * 1000), tick)

    w.after(300, tick)
    w.after(300000, w.destroy)          # chốt an toàn
    w.mainloop()
    if err:
        raise RuntimeError(err[0])
    log("OK - giao dien 3D")
    if os.environ.get("SHOTS_ANNOT"):       # tạm: gửi ảnh nhỏ qua annotation để xem từ xa
        import base64
        import io
        from PIL import Image
        for nm in ("2_3d_toan_mong.png", "4_3d_cat_1_4.png", "5_3d_phong_to.png"):
            im = Image.open(os.path.join(OUT, nm)).convert("RGB")
            im.thumbnail((1100, 700))
            b = io.BytesIO()
            im.save(b, "JPEG", quality=55)
            t = base64.b64encode(b.getvalue()).decode()
            n = (len(t) + 59999) // 60000
            for i in range(n):
                print(f"::notice title=IMG {nm} {i + 1}/{n}::" + t[i * 60000:(i + 1) * 60000])


if __name__ == "__main__":
    import traceback
    try:
        main()
    except BaseException:
        log(traceback.format_exc())
        LOG.close()
        txt = open(os.path.join(OUT, "log.txt"), encoding="utf-8").read()[-6000:]
        print("::error title=ui_smoke::" + txt.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
        sys.exit(1)
