# SplintFit v3.1 — 2026-10-20

## Sửa lỗi đã tái hiện

- Nhấn góc nhìn khi mới đặt một đầu nẹp: trước đây phát sinh ValueError ngoài Qt slot; nay báo rõ cần chọn đủ mốc, giữ ca đang mở.
- Tự cập nhật: hủy timer và yêu cầu dựng đang chờ khi thông số/xác nhận đổi; không tự gọi dựng với xác nhận đã mất hiệu lực.
- Dự án: từ chối tên vùng nâng sai kiểu, boolean/chuỗi trong tọa độ và thông số số, vùng nâng ngoài giới hạn UI; kiểm nhãn bao phủ khớp góc đã lưu trước khi thay ca.
- Dự án cũ không có tên vùng nâng: bổ sung tên mặc định trước khi đưa vào UI. Kiểm tra dữ liệu trên bản sao, không sửa trực tiếp đầu vào.
- Nạp file thất bại trước khi có mô hình: có nút lấy báo cáo ngay bước 1; báo cáo giữ lỗi, thao tác, file đang thử nạp và phiên bản runtime.

## Phát triển cho vỏ hai mảnh

- Kiểm tiếp xúc/giao tam giác bằng VTK first-contact, thêm kiểm bao chứa lấy mẫu theo hai hướng. Nếu không kiểm xong hoặc phát hiện vấn đề thì giữ vùng xem trước và chặn xuất.
- Xuất thêm `shell_piece_1_prototype.stl`, `shell_piece_2_prototype.stl` cùng hai mặt trong riêng; vẫn giữ STL tổng hợp và hai OBJ.
- JSON báo cáo có danh sách từng mảnh, tên file và báo cáo riêng.
- Thêm ví dụ hai mảnh và mesh OBJ tổng hợp để thử nhập.

## Kiểm chứng

59 kiểm thử đạt trên Linux/Python 3.12, gồm 46 test v3 và 13 test hồi quy/tích hợp mới. Tệp STL/OBJ/PLY thực được ghi và nạp lại trong kiểm thử. Kiểm UI dùng Qt offscreen, không kiểm GPU/chuột Windows. Đã chụp và xem panel thông số Qt; không có Fusion hoặc môi trường build Windows ở đây.

## Giới hạn còn lại

Chưa có mesh lỗi cụ thể của người dùng, chưa có exe Windows đã chạy thử, chưa Convert/Edit Form thật trong Fusion. T-Spline có thể thay đổi độ khít; cage vẫn chia tam giác thành ba quads. Chưa có kiểm tự giao mỗi vỏ, khe nhỏ nhất, đai/lỗ/bo tự động, áp lực/độ bền hoặc kiểm định lâm sàng. Kiểm giữa hai mảnh là sàng lọc hình học có giới hạn số học/lấy mẫu, không phải chứng minh an toàn.

Tài liệu API đã đối chiếu: [PyVista collision](https://docs.pyvista.org/api/core/_autosummary/pyvista.polydatafilters.collision), [decimate_pro](https://docs.pyvista.org/api/core/_autosummary/pyvista.polydatafilters.decimate_pro).
