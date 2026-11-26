# SplintFit Studio Desktop (v3.0)

Ứng dụng máy tính Windows độc lập (**PyQt6 + PyVistaQt**, không cần trình duyệt) hỗ trợ thiết kế bán tự động **nẹp cổ tay–cẳng tay in 3D cá thể hóa** từ file scan 3D (KIRI Engine), tối ưu cho **Bác sĩ & Kỹ thuật viên** và kết hợp trực tiếp với **Autodesk Fusion 360 (chế độ Form / T-Spline)**.

## Cấu trúc thư mục gọn sạch
- `desktop/`: Giao diện ứng dụng Windows gốc (`main_window.py`, `theme.py`) với quy trình 5 bước, 3 thanh trượt vùng an toàn 3D, 4 nhóm thẻ lâm sàng và hộp thoại chọn thư mục Windows gốc.
- `engine/`: Lõi xử lý hình học 3D (`geometry.py`, `cast_template.py`, `measurements.py`, `FUSION_FORM.md`, `fusion/SplintFitImport/`).
- `sample_data/`: Mẫu quét thử nghiệm.
- `tests/`: Kiểm thử tự động end-to-end (`test_desktop_app.py`).
- `START_STUDIO.bat`: File khởi động ứng dụng máy tính bằng 1 lần nhấp đúp.

## Khởi chạy nhanh (Windows)
1. Nhấp đúp `START_STUDIO.bat` (dùng Python 3.12 với `PyQt6`, `pyvista`, `pyvistaqt`, `numpy`, `scipy`).
2. Hoặc chạy lệnh:
```bash
python desktop/main_window.py
```

## Kiểm thử tự động
```bash
python -m unittest discover -s tests -v
```

Xem hướng dẫn thao tác chi tiết và giải thích toàn bộ thông số tại [USER_GUIDE.md](USER_GUIDE.md).  
Xem nhật ký phát triển chuẩn Capstone tại [LABNOTE.md](LABNOTE.md).
