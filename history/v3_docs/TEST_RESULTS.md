# Kiểm thử SplintFit v3.2 — 2026-10-20

**73 kiểm thử đạt** trên Linux/Python 3.12. Bộ v3.1 gồm 59 test, bổ sung 14 hành trình người dùng trong `tests/test_guided_ui_v32.py`.

```text
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
Ran 73 tests in 8.474s
OK
```

Các hành trình mới kiểm: nạp file qua guide; không tự xác nhận; chọn ba mốc liên tiếp; hủy callback khi đổi bước/chọn thủ công/đóng app; tiếp tục mốc còn thiếu; đi tới xuất khi chưa tạo mô hình; nhập người kiểm tra/xác nhận/xuất thật/mở đúng thư mục; lưu JSON không giả xuất 3D; vùng xem trước không thể đi tiếp; đổi hồ sơ xóa xác nhận cũ; số đo lệch đưa tới ô cần kiểm; truyền nhãn mốc không bắt chuột vào scene.

`pip check` không phát hiện phụ thuộc hỏng; compile Python thành công. Đã kiểm bố cục Qt tại 1366×740 cho cả 5 bước, với viewport 3D ẩn và ghi rõ trong ảnh kiểm tra nội bộ. Dải hướng dẫn/nút chính nhìn thấy ở cả 5 bước.

**Giới hạn:** Qt offscreen không hỗ trợ OpenGL ở môi trường này. Kiểm trạng thái/callback và scene giả không thay thế thử chuột, chữ/nhãn 3D hay GPU trên Windows. Chưa chạy launcher/build Windows, chưa chạy Fusion, chưa có mesh lỗi cụ thể của người dùng và chưa kiểm định lâm sàng. Thuật toán hình học giữ từ v3.1.

---

# Lịch sử kiểm thử v3.1

# Kiểm thử SplintFit v3.1 — 2026-10-20

**59 kiểm thử đạt** trên Linux/Python 3.12. NumPy 2.3.5, PyVista 0.49.0, PyVistaQt 0.13.1, PyQt6 6.11.0, VTK 9.3.1. Bộ v3 gồm 46 test; thêm 13 test trong `tests/test_regressions_v31.py`.

```text
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
Ran 59 tests in 5.658s
OK
```

`python -m pip check`: không có phụ thuộc hỏng. Compile app, geometry, measurements, project_io, build_windows và script Fusion thành công.

## Nội dung kiểm

| Nhóm | Số test | Phạm vi |
|---|---:|---|
| Hình học gốc/v2 | 16 | Scan hở, lỗ trong/ngoài vùng, nghiêng/dịch, quads, vùng nâng, nhiều mảnh, hai phần vỏ |
| Đo/kiểm hình học v3 | 8 | Chu vi, vòng hở/đa vòng, khóa xuất lệch chu vi, khoảng cách, hướng, điểm trong thành vỏ, merge normals, ghi xuất nguyên tử |
| UI gốc | 6 | Worker, trạng thái cũ, undo, chế độ, xác nhận kích thước, lưu/mở/xuất |
| UI v3 | 8 | Đổi mảnh/số đo/mặt phẳng, JSON lỗi, hash nguồn, người kiểm tra, rescale |
| Dự án v3 | 5 | Schema, kiểu/giới hạn, ghi nguyên tử, hash, khác ổ Windows qua giả lập |
| Fusion bridge | 3 | JSON mm/deg, từ chối đầu vào lỗi, rollback API giả lập |
| Hồi quy/tích hợp v3.1 | 13 | STL/OBJ/PLY, point cloud, STL riêng/JSON hai mảnh, giao/bao chứa, khe 0 khóa xuất, relief sai/cũ, nhãn bao phủ, góc nhìn thiếu mốc, timer, báo cáo lỗi khi chưa có mesh, giữ ca khi JSON lỗi |

Đã tạo lại hai bộ xuất từ mẫu tổng hợp: `example_export` (1 mảnh), `example_bivalve_export` (2 mảnh). Kiểm thêm các vỏ hai mảnh ở góc xoay 0°, 37°, 90°: dựng được và không phát hiện tiếp xúc theo bộ kiểm hiện có. Panel thông số Qt được chụp và xem; file `Parameters_preview.png` không chứng minh viewport 3D hoạt động.

## Chưa kiểm chứng

- Chưa có mesh KIRI lỗi thực tế của người dùng.
- Qt offscreen không tạo được OpenGL context; test trạng thái/callback tắt render, không xác nhận GPU, chuột hoặc viewport Windows.
- Chưa chạy PyInstaller trên Windows; `BUILD_WINDOWS.bat` là recipe, gói không chứa exe Windows đã kiểm chứng.
- Chưa chạy Autodesk Fusion: test bằng API giả không thay thế Import/Convert/Edit Form/Thicken thật.
- Chưa kiểm tự giao từng vỏ, khe nhỏ nhất, độ dày nhỏ nhất, áp lực, độ bền hoặc an toàn lâm sàng. Kiểm tiếp xúc giữa hai mảnh có giới hạn số học và bao chứa lấy mẫu.
- Hash/nhật ký không phải chữ ký điện tử hoặc hồ sơ chống sửa đổi.
