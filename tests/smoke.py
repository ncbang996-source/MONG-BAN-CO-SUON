"""Kiểm tra nhanh: đọc Excel mẫu, dựng 2 tờ, xuất PDF + DXF + Excel khối lượng, so với Excel mẫu."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from mongban import export, kl_excel, model  # noqa: E402

p, warn = model.read_excel(os.path.join(ROOT, "samples", "D122-42_MB4-10x12-2.5.xlsm"))
assert not warn, warn
# khối lượng theo sheet "KL be tong" của Excel mẫu
assert abs(model.vol_mong(p) - 60.837) < 0.001
assert abs(model.vol_lot(p) - 12.38) < 0.001
assert abs(model.vol_dao(p) - 430.42) < 0.001 and abs(model.vol_dap(p) - 188.533) < 0.001
assert abs(model.vol_cat(p) - 173.57) < 0.001 and abs(model.area_vai(p) - 368.732) < 0.001
assert abs(model.area_vk(p) - 97.268) < 0.001
res = export.build(p, os.path.join(ROOT, "assets", "frames", "KT-A3.dxf"))
kgs = {int(d): w for d, _, w in res.geo.klc}
# thép bản Ø14 khớp sheet "KL thep mong"; Ø25 theo quy tắc cắt thép dầm = 1/2 ô ngoài của từng dầm, làm tròn
# lên 100, tính từ mép móng (thanh ngắt 7200 / 8200 thay vì 7250 / 9250 của Excel:
# 3004.00 + 32 thanh x 0.15 x 3.85 = 3022.48)
assert abs(kgs[14] - 3914.79) < 0.05 and abs(kgs[25] - 3022.48) < 0.05, kgs
d = tempfile.mkdtemp()
export.save_dxf(res, os.path.join(d, "t.dxf"))
data = export.pdf_bytes(res)
assert data[:4] == b"%PDF" and len(res.origins) == 2
print("OK - thep", round(sum(kgs.values()), 2), "kg; PDF", len(data), "bytes")
kl_excel.export(p, res.geo, os.path.join(d, "kl.xlsx"))
# giai đoạn TKCS: 1 tờ
p2 = dict(p, GD="TKCS")
assert len(export.build(p2).origins) == 1
print("OK - Excel khoi luong, TKCS")
# đắp móng hđđ, đối trọng hđt (néo góc: 1/2 móng; chọn ô bản); hình học đối trọng đã đối chiếu bằng shapely
p3 = dict(p, HT=1, HDT=0.5, HDD=0.5)
assert abs(model.vol_dt(p3) - 24.255) < 0.001 and abs(model.vol_dd(p3) - 64.687) < 0.001
assert abs(model.vol_dt(dict(p3, DT_MODE=1, DT_SEL="136")) - 10.25) < 0.01
assert model.vol_dt(dict(p3, HT=0)) == 0.0
res3 = export.build(dict(p3, DT_MODE=1, DT_SEL="2346"))
assert export.pdf_bytes(res3)[:4] == b"%PDF"
print("OK - dap mong, doi trong")
