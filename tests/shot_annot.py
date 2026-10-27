"""Tạm thời: gửi 1 ảnh chụp giao diện (nén nhỏ) qua annotation của GitHub Actions."""
import base64
import io
import os
import sys

from PIL import Image

im = Image.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shots", sys.argv[1]))
im = im.convert("RGB")
for q, side in ((45, 800), (35, 700), (30, 600), (25, 520)):
    t = im.copy()
    t.thumbnail((side, side))
    b = io.BytesIO()
    t.save(b, "JPEG", quality=q)
    s = base64.b64encode(b.getvalue()).decode()
    if len(s) <= 9 * 4000:
        break
n = (len(s) + 3999) // 4000
for i in range(n):
    print(f"::notice title=IMG {sys.argv[1]} {i + 1}/{n}::" + s[i * 4000:(i + 1) * 4000])
