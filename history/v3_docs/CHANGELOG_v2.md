# Thay đổi theo phản hồi — v2

## v2.1 — làm rõ bước xác nhận kích thước

- Đặt ô xác nhận sau phần đối chiếu số đo, giải thích thao tác áp dụng số đo và xác nhận lại sau hiệu chỉnh.
- Khi chưa xác nhận, nút Tạo / Cập nhật nẹp đưa về bước 1 và chỉ rõ tên ô cần tích.
- Giữ kiểm tra kích thước trước khi dựng nẹp; chọn mốc vùng nẹp và nhập giá trị không tự xác nhận kích thước.
- Bổ sung kiểm thử: đủ mốc và đã nhập số đo vẫn bị chặn khi chưa xác nhận; xác nhận xong mới khởi chạy dựng nẹp.

| Vấn đề của bản đầu | Cách xử lý trong v2 |
|---|---|
| X/Y/Z và % chiều dài khó dùng, mesh nghiêng khó chạy | Hai đầu nẹp và điểm mặt đặt trên da; chiều chỉnh bằng mm; trục theo vùng chọn |
| Mọi tham số lưới xuất hiện trong màn hình cơ bản | Tab Độ vừa và Tránh tì đè; tab Kỹ thuật chỉ ở Nâng cao |
| Nhập mesh lớn chạy trên luồng UI | Đọc, phân tích, chuẩn bị bề mặt trong worker |
| File nhiều mảnh hoặc chứa nhiều đối tượng bị từ chối | Hợp nhất dữ liệu đọc, thống kê mảnh, cho chọn bề mặt; giữ nguồn tham chiếu |
| Mặt trùng/mặt không có diện tích làm dừng | Loại mặt lỗi cơ bản, không lấp giải phẫu |
| Lỗi nơi không đặt nẹp chặn cả thiết kế | Kiểm chính trên vùng thực sự được chọn |
| Thiếu dữ liệu chỉ hiện thông báo rồi dừng | Giữ vùng xem trước, hiện biên, khóa xuất có lý do |
| Giới hạn số quads chặn cả shell | Phân biệt Form sẵn sàng và shell sẵn sàng |
| Thông số lâm sàng ít, mang tính preset | Ghi chỉ định/tư thế; điều chỉnh đệm, khoảng chừa, độ dày, bao phủ và nâng cục bộ thực |
| Chỉ có máng nửa chi | Thêm mức bao phủ và hai mảnh với khe mở |
| Chưa có chấm mốc thật, undo/redo | Picking trên bề mặt, chiếu về mesh đầy đủ, lịch sử vùng/thông số |
| Khó truy ra lý do mesh thất bại | Log thực và báo cáo chẩn đoán JSON |

Chưa hoàn thành trong app: đai/lỗ thoáng/bo mép, retopology tối ưu, native `.f3d`, add-in parametric, kiểm tự giao/độ bền/áp lực. Các yêu cầu hoàn thiện Fusion được gắn nhãn riêng trong UI và JSON.

Các trường giai đoạn/chỉ định/tư thế là hồ sơ; không tự chọn điều trị. Máng lòng/lưng là nhãn người dùng cùng điểm mặt đặt, chưa nhận diện giải phẫu tự động.
