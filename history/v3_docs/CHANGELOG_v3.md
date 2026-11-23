# SplintFit v3.0

## Lỗi đã sửa

- Đổi mảnh quét xóa xác nhận kích thước, mốc đo A–B, nhãn số đo và người kiểm tra cũ.
- Đổi A–B hoặc số đo tham chiếu yêu cầu kiểm tra/xác nhận lại, vô hiệu hóa kết quả trước.
- Hiệu chỉnh tỷ lệ giữ đúng mảnh đang chọn, xóa mốc/chu vi theo hệ tọa độ cũ; kể cả mẫu tổng hợp cũng phải xác nhận lại sau hiệu chỉnh.
- Đổi nhãn máng lòng/lưng không tự xóa xác nhận ba mốc khi điểm đặt không thay đổi. Hình học mới vẫn cần tạo/kiểm tra lại.
- Cảnh báo chỉ rõ mốc/ô xác nhận còn thiếu; có dòng trạng thái trước nút tạo.
- Không cho bắt điểm trong khi worker đang đọc/dựng; dừng timer khi bắt đầu worker; không tự gọi dựng khi xác nhận đã mất hiệu lực.
- Kiểm tra dự án trước khi áp dụng: kiểu dữ liệu, tọa độ, số hữu hạn, giới hạn giao diện, kiểu nẹp và yêu cầu hoàn thiện.
- Dự án mới ghi SHA-256 file nguồn. Khi file đã thay đổi, chặn áp mốc cũ. Dự án cũ chưa có hash vẫn cần kiểm lại và xác nhận.
- Lưu JSON bằng file tạm + thay thế; hỗ trợ tham chiếu mesh ở ổ đĩa khác trên Windows.
- Xuất gói qua thư mục tạm: lỗi ghi không để lại thư mục có vẻ đã xuất hoàn chỉnh.
- Log chuyển tới thư mục người dùng, phục vụ bản đóng gói và thư mục app không có quyền ghi.
- Gắn normal theo dữ liệu đỉnh khi ghép hai mảnh, không giả định thứ tự merge của VTK; báo cáo số mặt/khoảng cách/sai số tổng hợp cả hai mảnh.

## Bổ sung

- Khoảng cách không dấu đo từ đỉnh mặt trong đến mesh quét cho bản đồ màu; vẫn lưu khoảng chừa danh nghĩa riêng.
- Sàng lọc hướng quay vào trục; sàng lọc điểm quét nằm trong thành vỏ kín. Ứng viên từ signed distance được xác minh bằng winding solid angle vì góc lõm có thể làm dấu khoảng cách sai.
- Đo chu vi ba mặt cắt trên dữ liệu thật. Chỉ báo chu vi khi có đúng một vòng kín; không nội suy/khép vòng hở.
- Nhập số đo thước dây cùng mặt phẳng; giữ vỏ xem trước và chặn xuất khi lệch ngưỡng hoặc không thể đo vòng. Số 0 là chưa nhập, không giả đạt.
- Xóa số đo chu vi khi đổi mặt phẳng đo; hiển thị ba mặt cắt tím ở bước 4; thêm CSV kết quả.
- Nhật ký load/rescale/build/save/open/export-request; người kiểm tra và thời điểm kiểm tra khi xuất. Nhật ký này không phải chữ ký điện tử chống sửa đổi.
- `fusion_user_parameters.json` và script Fusion nhập/cập nhật 8 User Parameters, đơn vị mm/deg tường minh. Script không tự dựng Form.
- Cấu hình VS Code, kiểm thử Windows và recipe đóng gói PyInstaller.

## Chưa hoàn thành

Đai, lỗ thoáng, bo mép tự động; cage quad tối ưu; tự giao toàn bề mặt, độ dày nhỏ nhất thực, va chạm giữa hai mảnh; mô phỏng áp lực/độ bền; nẹp ngón/spica/khuỷu gập; điều trị tự động theo giai đoạn; kiểm định lâm sàng. Chưa tạo `.f3d` trực tiếp, chưa đồng bộ hình học Form theo JSON.
