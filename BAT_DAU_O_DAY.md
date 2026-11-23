> Bản GitHub chỉ chứa source. Để tạo lại gói demo trước bước xem HTML: chạy python build_demo.py --output demo_export, hoặc mở app và chọn mẫu mô phỏng.

# Bắt đầu sử dụng SplintFit Cast Prototype v4.0

## 1. Xem mẫu trước, không cần cài đặt

Giải nén toàn bộ ZIP. Vào demo_export, mở XEM_MAU_3D.html bằng Edge/Chrome/Firefox.
Kéo để xoay, cuộn để phóng to. Bật/tắt Mảnh 1, Mảnh 2 và Scan tham chiếu.

Đây là hình học đã xuất thật từ dữ liệu mô phỏng, không phải tay bạn. Trang này chỉ xem; muốn dựng trên scan khác, chạy app ở bước 2.

## 2. Mở ứng dụng trên Windows

Cần Python 3.11 hoặc 3.12 bản 64-bit. Nếu cài Python lần đầu, chọn Add Python to PATH.
Giải nén vào thư mục mới, ví dụ D:\\SplintFit_Cast_Prototype.
Mở đúng thư mục có app.py và START_WINDOWS.bat.
Nhấp đúp START_WINDOWS.bat. Lần đầu cần Internet để cài thư viện.
App mở thành cửa sổ riêng, không phải Streamlit.

Nếu chạy qua VS Code: File > Open Folder > chọn thư mục chứa app.py. Mở Terminal và chạy từng dòng:

    py -3.12 -m venv .venv
    .venv\\Scripts\\python.exe -m pip install -r requirements.txt
    .venv\\Scripts\\python.exe app.py

Nếu chỉ có Python 3.11, thay dòng đầu bằng py -3.11 -m venv .venv.
Các lần sau chỉ chạy dòng cuối. Không cần Activate hoặc đổi Execution Policy.

## 3. Làm một ca mô phỏng trước

1. Ở bước Nạp file & kích thước, bấm Thử mẫu nẹp cổ tay có lỗ.
2. App nạp mẫu tổng hợp và chuẩn bị mốc. Các xác nhận được đặt sẵn chỉ cho mẫu mô phỏng có kích thước biết trước.
3. App chuyển tới Tạo mô hình nẹp. Bấm Tạo / Cập nhật nẹp hoặc nút hướng dẫn phía trên.
4. Chờ dựng xong. App mở Xem kết quả. Bật Vỏ nẹp, tắt Chi quét nếu muốn nhìn rõ lỗ.
5. Muốn đổi lỗ: trở về bước Tạo mô hình nẹp > tab Dáng & lỗ.
6. Chỉnh Khoảng bố trí danh nghĩa để đổi mật độ; Tỷ lệ lỗ trên ô để đổi kích thước tương đối.
7. Cửa ngón cái của mẫu: độ sâu 35 mm chỉ là ví dụ. Đổi góc để di chuyển đường khuyết quanh tay.
8. Bấm Tạo / Cập nhật nẹp sau mỗi thay đổi. Kết quả cũ không được dùng để xuất.
9. Qua bước Xuất mô hình 3D. Nhập tên người kiểm tra và đánh dấu đã xem vùng/số đo/hướng.
10. Bấm Xuất mô hình 3D rồi chọn thư mục chứa kết quả.
11. Bấm Mở thư mục kết quả. Mở XEM_MAU_3D.html để kiểm file xuất.

Mẫu đi kèm dự kiến có 24 lỗ thoáng và 12 khe luồn đai trên hai mảnh. Nếu thay thông số, số lượng sẽ đổi. Khe luồn đai vẫn được tạo khi tắt lỗ thoáng.

## 4. Dựng từ scan của bạn

1. Chọn đơn vị xuất từ KIRI trước khi nạp: mm, cm hoặc m. Không biết đơn vị thì đối chiếu bằng kích thước thực, không đoán.
2. Chọn file STL/OBJ/PLY. Nếu nhiều mảnh, chọn bề mặt tay phù hợp.
3. Kiểm kích thước bằng số đo độc lập. A–B là khoảng cách thẳng, không phải chu vi.
4. Khi đã kiểm đúng, đánh dấu Đã đối chiếu đúng kích thước thực.
5. Qua Chọn vùng làm nẹp > Bắt đầu chọn 3 mốc.
6. Nhấp chuột phải lần lượt: đầu nẹp phía khuỷu; đầu nẹp phía bàn tay; một điểm ở giữa mặt muốn đặt nẹp.
7. Xoay hình xem vị trí 1/2/3, rồi xác nhận vùng. Trục nối hai đầu chỉ giúp dựng hình, không tự nắn tư thế tay.
8. Chọn Nẹp hai mảnh. Trong Dáng & lỗ, bật Tạo mẫu nẹp có cấu trúc cho Fusion Form.
9. Nếu scan chỉ có cẳng tay, để độ sâu cửa ngón cái = 0. Nếu có bàn tay, đặt cửa thủ công và kiểm vị trí theo mẫu chuyên môn.
10. Chọn đệm, khoảng chừa, độ dày và khe mở. Các số mặc định chưa phải chỉ định điều trị.
11. Tạo mô hình, xem từng mảnh và báo cáo. Khi không đủ dữ liệu, app giữ vùng xem trước và chặn xuất.
12. Chỉ xuất khi đã xử lý các lỗi. Đọc FUSION_FORM.md để chuyển sang Fusion.

Engine hiện tại yêu cầu mặt cắt một vòng kín, dạng hướng tâm. Không chọn qua vùng tách thành nhiều ngón. Không có thuật toán tự khôi phục phần bàn tay bị thiếu.

## 5. Chọn đúng file sau khi xuất

- shell_piece_1_prototype.stl và shell_piece_2_prototype.stl: vỏ có lỗ và độ dày, dùng để kiểm hình học/chuyển slicer.
- splint_form_piece_1_quad.obj và splint_form_piece_2_quad.obj: mặt nền ít phức tạp, không có lỗ, dùng kéo chỉnh dáng trong Form.
- splint_form_perforated_piece_1_quad.obj và ...piece_2...: mặt trong quad có lỗ và khe đai, dùng thử Convert và chỉnh trực tiếp trong Form.
- scan_reference_mm.stl: scan tham chiếu trong cùng hệ tọa độ.
- inner_piece_1_reference_mm.stl và ...piece_2...: mặt trong tham chiếu trước T-Spline smoothing.
- fusion_user_parameters.json: thông số cho script Fusion; chưa tự thay đổi Form.
- parameters_and_report.json: báo cáo thông số và giới hạn phép kiểm.
- XEM_MAU_3D.html: xem offline hình học từ gói xuất.
- Lưu dự án JSON trong app: lưu để làm tiếp; không thay thế OBJ/STL.

Đầu ra chỉ là prototype nghiên cứu. Trước thử vật lý cần hoàn thiện mép, vật liệu, đệm–đai và kế hoạch kiểm phù hợp.

## 6. Khi gặp lỗi

Giữ cửa sổ Terminal để đọc lỗi. App có nút Xuất báo cáo lỗi nạp file / Xuất báo cáo để kiểm tra lỗi.
Gửi báo cáo và mesh lỗi để tái hiện. Kiểm tra đang mở đúng thư mục v4, không dùng app.py hoặc môi trường .venv từ bản khác.

Nếu báo thiếu dữ liệu: thu vùng, chọn lại bề mặt hoặc quét bổ sung. Không tăng khoảng chừa để che lỗi scan.
Nếu báo nhiều contour: giới hạn dưới các ngón hoặc cần thiết kế chuyên biệt.
Nếu Convert trong Fusion thất bại: thử OBJ nền, giữ quads khi import và kiểm Repair Body; không coi STL có rất nhiều tam giác là Form đã chỉnh được.
