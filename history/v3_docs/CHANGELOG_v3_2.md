# SplintFit v3.2 — Hướng dẫn theo toàn bộ quy trình

## Vấn đề được xử lý

Người dùng có thể đi tới bước 4/5 mà chưa tạo mô hình; nút tạo nằm dưới bảng cuộn và Lưu JSON bị hiểu là xuất mô hình. Chọn từng mốc bằng các nút tách rời khiến thứ tự khó nhớ.

## Thay đổi

- Thêm dải hướng dẫn cố định trên cùng. Nút chính phụ thuộc trạng thái: chọn file, tới ô xác nhận kích thước, chọn mốc, xác nhận vùng, tạo mô hình, xem kết quả, nhập người kiểm tra, xác nhận đã xem, xuất, mở thư mục.
- Nút Tiếp kiểm dữ liệu còn thiếu và đưa về đúng bước. Không tự tích các xác nhận kích thước/vùng/kiểm tra.
- Chọn 3 mốc liên tiếp, nhắc từng lần chuột phải. Nhãn số trên hình. Có dừng chọn, hủy callback chờ khi đổi bước, chọn thủ công, đổi mảnh, undo hoặc đóng app.
- Thu gọn hiệu chỉnh kích thước, hồ sơ thêm, đối chiếu chu vi và ghi chú Fusion. Các dữ liệu không bị tự bỏ qua; số đo đã nhập vẫn chặn xuất khi không đạt đối chiếu.
- Báo cáo lỗi/số đo đưa lên trước; guide có thể mở đúng ô chu vi đang lỗi. Vỏ tự hiển thị sau dựng.
- Diễn giải tổng chừa cơ bản theo đệm + chừa thêm, có tooltip. Không tự đổi theo chẩn đoán/giai đoạn.
- Đổi tên Lưu dự án JSON và Xuất mô hình 3D, giải thích chức năng. Sau xuất có đường dẫn/nút mở thư mục.
- Cửa sổ chọn kích thước theo màn hình, điều chỉnh bề rộng panel. Kiểm bố cục Qt ở 1366×740 với viewport 3D ẩn.
- Launcher Windows thử Python 3.12, 3.11 rồi python hiện có. Recipe chưa chạy trực tiếp trên Windows.
- Thêm `BAT_DAU_O_DAY.md`, hướng dẫn trong nút Cách dùng.

## Phạm vi

Giữ thuật toán hình học và điều kiện xuất của v3.1. Chưa có scan lỗi thật của người dùng. Chưa kiểm chuột/GPU Windows, launcher Windows hay Convert trong Fusion. Kiểm UI ở đây dùng Qt offscreen; nhãn được kiểm qua lời gọi scene, không chứng minh hiển thị/độ đọc trên mọi GPU. Chưa kiểm định lâm sàng.

API đối chiếu: [PyVista add_point_labels](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.plotter.add_point_labels), [Qt QScrollArea](https://doc.qt.io/qt-6/qscrollarea.html).
