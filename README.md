# VE_MONGBANCOSUON

App Windows chạy offline, vẽ nhanh bản vẽ **móng bản có dầm (móng bản có sườn)** cho móng cột đường dây từ file Excel. Kiến trúc và cách dùng giống app VE_MONGBANKOSUON.

## Chức năng
- **Đọc Excel:** lấy số liệu từ sheet `TONG HOP` (các ô liệt kê bên dưới).
- **Hiệu chỉnh:** sửa mọi thông số trên giao diện. App kiểm tra số liệu và cập nhật khối lượng ngay.
- **Khung tên:** mặc định dùng `assets/frames/KT-A3.dxf` (block KHUNG_TEN). App điền attribute nếu có, nếu không thì điền theo toạ độ. Logo OLE được chèn vào PDF.
- **Bản vẽ:**
  - TKCS có 1 tờ: mặt cắt A-A, mặt bằng móng, bảng tổng kê.
  - TKBVTC có 2 tờ.
    - Tờ 1/2: mặt cắt A-A, mặt bằng móng có thép bản và thép dầm, bảng thống kê cốt thép.
    - Tờ 2/2: mặt cắt dầm 1-1 và 2-2 (1:25), vát nách 3-3 và 4-4 (1:50), cổ móng 5-5 kèm thang leo, lưới thép đầu trụ, 1/2 mặt cắt B-B dọc tim dầm (thép dầm, neo thép cổ móng), bảng tổng kê.
- **Xuất file:** PDF A3, AutoCAD DXF, Excel khối lượng (`_KL.xlsx`, gồm các sheet TONG KE, THONG SO, KHOI LUONG). Tên file xuất trùng tên file Excel. Trong Excel, chiều dài và số lượng từng thanh thép đều là công thức theo thông số, có diễn giải: sửa ô thông số thì khối lượng tự tính lại.
- **Mô hình 3D:** tab riêng trong khung xem, bê tông trong suốt, bật/tắt từng nhóm thép, cắt 1/4 móng.
- **Sắp xếp (kéo thả):** giống app cũ. Vị trí lưu vào `<tên Excel>.layout.json`.

## Ô đọc từ sheet TONG HOP
| Ô | Thông số | Ô | Thông số |
|---|---|---|---|
| B3 | Hình thức cột (ĐỠ / NÉO / NÉO DỪNG) | C3, C4, C5 | Tên cột, tên móng, giai đoạn |
| K3, K4 | Bê tông móng, bê tông lót | K5 | Mã bản vẽ ghi chú chung |
| K7, K8 | L1, L2: tim chân cột, cũng là tim dầm | K10, K11 | B, L |
| K13, K14 | a: rộng dầm, h: cao dầm (tính cả bản) | K16 | h1: dày bản |
| K17 | c: cạnh lỗ mở ở tim móng | K18 | e: cạnh vát nách chỗ giao dầm |
| K20 | b: cạnh cổ móng | K28, K30 | H1: chôn sâu, H2: cao trên mặt đất |
| K34, K35 | Lớp bảo vệ đáy / còn lại (mm) | K36, K37 | hđđ, hđt (chưa hỗ trợ, phải bằng 0) |
| K39, K40, K41 | Đệm cát, hệ số mái, mở rộng đáy hố | K42 + L42 | Bu lông neo |
| C44 / D44, D45 | Thép bản: Ø / bước (cm) ở ô 2 cạnh và ô 4 cạnh ngàm | I44 / J44, J45 | Thép chống: Ø / bước (cm) |
| C48 / D48 | Thép chủ cổ móng: Ø / số thanh | C49..D51, F51 | Đai cổ, đai phụ cổ, lưới đầu trụ, số lớp |
| I48 / J48 | Thép chủ dầm: Ø / số thanh 1 mặt | I49..J51 | Đai dầm, đai phụ dầm, thang leo |
| | Thép giá dầm: Ø = thép bản; số thanh theo TCVN 5574:2018 mục 10.3.3.3 (h > 700) | | |

## Quy tắc tính
- **Khối lượng bê tông, lót, đào, đắp, đệm cát, ván khuôn, vải địa:** theo công thức sheet `KL be tong` của Excel mẫu. Vải địa trải phẳng thành 1 tấm chữ nhật. Mái hố đào vẽ 1:0.5.
- **Đền bù:** rộng B + 1, dài L + 1.
- **Thép:** số thanh và chiều dài theo quy tắc sheet `KL thep mong`, khối lượng tính từ đúng các thanh vẽ ra.
  - Thép bản theo phương cạnh dài nằm lớp ngoài cùng. Thanh chống đặt theo phương cạnh ngắn.
  - Thép chủ dầm: số thanh dài suốt mỗi mặt là n/2 (n chia hết 4) hoặc INT(n/2) + 1, số còn lại là thanh ngắt. Thanh ngắt cắt mỗi đầu ½ khoảng mép dầm → mép móng, làm tròn lên 100, tính từ mép móng. Từ 10 thanh trở lên thì cắt so le.
  - Khoảng hở ngang thép chủ ≥ 40 mm, không đủ thì thêm hàng (hàng dưới tối thiểu 2 thanh). Hàng dưới > 2 thanh thì chọn "các hàng đều nhau" hoặc "đầy hàng ngoài".
  - Đoạn neo thép chủ cổ móng cố định 500. Thang leo đặt ở 2 trụ chéo nhau khi H2 > 1.5 m.

## Nét in (theo layer)
| Layer | Nét | Đối tượng |
|---|---|---|
| TRUC, HATCH | 0,13 | trục, hatch |
| DIM, CHU, HINH THUC, BANG | 0,18 | kích thước, chữ, leader, bảng |
| MAIN, MAT CAT, VAI DIA | 0,30 | bao móng, ký hiệu mặt cắt, vải địa |
| DAI | 0,35 | đai, thép phân bố, lưới |
| COTTHEP | 0,50 | thép chủ |

## Tải file .exe
Vào tab **Actions** của repo, mở lần build mới nhất và tải mục **VE_MONGBANCOSUON-exe** ở phần *Artifacts*.

## Chạy từ mã nguồn
```
pip install -r requirements.txt
python app.py
```

## Phát triển app cho loại móng khác
Xem [docs/HUONG_DAN_PHAT_TRIEN.md](docs/HUONG_DAN_PHAT_TRIEN.md): kiến trúc, module dùng lại / viết mới, quy ước vẽ, quy trình làm việc, quy tắc kỹ thuật đã chốt. Công cụ hỗ trợ:
- `python tools/render_preview.py [file.xlsx] [KEY=VAL ...] --out thư_mục`: render ảnh xem trước.
- `python tools/check_kl_excel.py`: đối chiếu công thức Excel khối lượng với chương trình (cần LibreOffice).
