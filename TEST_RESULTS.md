# Kết quả kiểm tra v4.0 prototype

Mốc: 20/11/2026. Môi trường Linux / Python 3.12.14.

## Kết quả đã quan sát

- 83 kiểm thử Python qua, gồm kiểm thử kế thừa và 10 kiểm thử mới cho template/UI.
- Mẫu tổng hợp: hai mảnh vỏ; 24 lỗ thoáng, 12 khe luồn đai; 7.264 tam giác tổng cộng.
- Mỗi mảnh: không có cạnh hở, cạnh không đa tạp, mặt suy biến hoặc cạnh sai hướng tại phép kiểm topology.
- Euler characteristic xác nhận các lỗ là đường xuyên qua thể tích vật liệu.
- Có kiểm chặn scan thiếu một tam giác trong ROI, đối chiếu chu vi, tọa độ sau dịch chuyển và vòng lưu/mở dữ liệu mẫu mới.
- OBJ xuất có mặt tứ giác cho cả phiên bản nền và perforated. STL được đọc lại để kiểm cạnh kín.
- Viewer offline: JavaScript qua kiểm cú pháp/DOM-canvas harness trên Node; vẽ 7.264 tam giác, bật/tắt mảnh và scan, xoay, zoom và reset qua.
- Ảnh PREVIEW_DEMO.png dựng từ tam giác STL thực bằng rasterizer CPU có z-buffer; đã kiểm bằng mắt.

## Chưa kiểm chứng

- Chưa chạy trực tiếp launcher và cửa sổ đồ họa trên Windows; chưa có EXE Windows đã thử.
- Kiểm thử Qt chạy headless; môi trường này không có X server/OpenGL cho kiểm hiển thị 3D desktop.
- Trình duyệt headless bị môi trường chặn khởi động, nên chưa xác nhận viewer trong trình duyệt thật tại đây. Node harness không thay thế phép thử đó.
- Chưa chuyển OBJ/Finish Form/Thicken trực tiếp trong Autodesk Fusion; nhãn trong báo cáo là NOT_TESTED_IN_FUSION.
- Chưa có file scan của người dùng, chưa in vật lý, chưa kiểm độ vừa, tự giao toàn bề mặt, độ bền hoặc lâm sàng.

## Phiên bản thư viện kiểm thử

- numpy: 2.3.5
- scipy: 1.17.0
- pyvista: 0.49.0
- vtk: 9.3.1
- PyQt6: 6.12.1
- pyvistaqt: 0.13.1

Chạy lại: python -m unittest discover -s tests -v. Viewer bổ sung: node tests/check_viewer.cjs demo_export/XEM_MAU_3D.html.

## 4.0.1 — kiểm lại ngày 23/11/2026

90/90 kiểm thử Python qua (16.474 giây). Thêm kiểm tái lập hình học cùng đầu vào và công cụ lab note. Viewer Node harness qua. Xem LAB_NOTES/LN-20261123-002_hole-pattern-and-versioning.md và verification/lab_unittest_20261123.log. Các giới hạn Windows/Fusion/độ bền/lâm sàng ở trên vẫn còn nguyên.
