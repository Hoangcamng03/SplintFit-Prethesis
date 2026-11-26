# SplintFit Studio

Ứng dụng web cục bộ (Local Web App) hỗ trợ thiết kế bán tự động **nẹp cổ tay–cẳng tay in 3D cá thể hóa** từ file scan 3D (KIRI Engine), tối ưu cho **Bác sĩ & Kỹ thuật viên** và kết hợp trực tiếp với **Autodesk Fusion 360 (chế độ Form / T-Spline)**.

## Tính năng chính (v2.0)
- **Nạp file scan 3D (`.stl`, `.obj`, `.ply`) không tự vá lỗ (No Hole Filling):** Kiểm tra độ phủ bề mặt, hiển thị biên hở màu đỏ và cho phép lọc mảnh rác.
- **Tự động khóa vùng an toàn (Safe-Zone) + 3 thanh trượt 3D 60fps:** Tự động nhận diện đoạn cẳng tay–cổ tay hợp lệ (tránh mép hở và tránh tách ngón cái/ngón tay), giúp chỉnh chiều dài & hướng tách 2 mảnh trực tiếp mà không gây lỗi đặt điểm.
- **Cấu hình lâm sàng trực quan:** 4 nhóm thẻ chọn nhanh (*Tình trạng tay*, *Độ cứng*, *Lưới tổ ong thoáng khí so le*, *Đường mở đầu bàn tay*) + mục mở rộng cho Kỹ thuật viên.
- **Lưới thoáng tổ ong so le & Loe mép chống cấn da (`rim_flare_mm`):** Đảm bảo vỏ kín (`watertight`), giữ khung biên đặc và 3 dải gia cường khe luồn dây đai Velcro.
- **Xuất gọn cho Autodesk Fusion 360 Form (T-Spline):** Xuất mặc định 5 file mesh chuẩn (`splint_form_piece_1_quad.obj`, `piece_2`, bản `perforated` All-Quad, và `scan_reference_mm.stl` cùng hệ tọa độ `mm`), hỗ trợ chọn thư mục lưu tùy ý trên Windows.

## Khởi chạy nhanh (Windows)
1. Cài Python 3.12 với các thư viện: `flask`, `pyvista`, `numpy`, `scipy`.
2. Nhấp đúp `START_STUDIO.bat` (hoặc chạy `python backend/server.py`).
3. Mở trình duyệt tại `http://127.0.0.1:8765`.

## Kiểm thử tự động
```bash
python -m unittest discover -s tests -v
```

Xem lịch sử tiến độ và quyết định kỹ thuật tại [LABNOTE.md](LABNOTE.md).
