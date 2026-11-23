# Cập nhật v3.2

Thêm hướng dẫn và nút hành động theo trạng thái, chọn mốc liên tiếp, mục thu gọn và xuất mô hình rõ ràng. Không thay thuật toán hình học hoặc tự bỏ qua xác nhận. Xem `CHANGELOG_v3_2.md` và `BAT_DAU_O_DAY.md`. Các bảng bên dưới giữ lịch sử đánh giá v3/v3.1.

# Cập nhật v3.1 — 2026-10-20

Bổ sung kiểm giao tam giác giữa hai vỏ bằng VTK và kiểm bao chứa lấy mẫu, khóa xuất khi phát hiện chạm/giao. Chưa chứng minh khe tối thiểu hay không tự giao từng vỏ. Sửa lỗi giao diện/dự án, thêm STL riêng và báo cáo lỗi ngay bước nạp. Chi tiết: `CHANGELOG_v3_1.md`; 59 kiểm thử đạt. Bảng dưới giữ đối chiếu bản v3 ban đầu, các dòng “chưa kiểm giữa hai mảnh” đã được cập nhật bằng bước sàng lọc v3.1 nêu trên.

# Đối chiếu lộ trình và bản sửa v3

Ngày: 2026-10-20. Nền tảng: bản ZIP v2.1 đã lưu trước đó, cập nhật thành v3.0. Không sửa hoặc đẩy lên repository GitHub.

## Phạm vi đã thực hiện

Giữ desktop PyQt6/PyVista và luồng 5 bước. Sửa trạng thái cũ, hiệu chỉnh số đo, lưu/mở và xuất gói; phát triển kiểm hình học có giới hạn, đối chiếu chu vi và chuyển tham số sang Fusion. Không triển khai toàn bộ giai đoạn 0–6 thành một thiết bị đã kiểm định.

| Giai đoạn trong kế hoạch | Trạng thái v3 | Phần còn cần làm |
|---|---|---|
| 0. Dữ liệu quét | Có đọc file, đổi đơn vị, chọn mảnh, đối chiếu A–B và chu vi | Bộ dữ liệu quét lặp, số đo độc lập, thống kê sai số; chưa nhận mesh lỗi của người dùng |
| 1. Lõi + Fusion | Cắt vùng trên tam giác theo mốc, offset/vỏ, quad OBJ; script User Parameters | Lưới quad có hướng tốt hơn và thử Convert/Edit Form trên Fusion thật; v3 chưa thay bằng cage mặt cắt có cấu trúc |
| 2. Giao diện | Có UI, worker, tiến độ, lưu/mở JSON, undo/redo, xuất | Kiểm tương tác chuột/GPU trên Windows và thử khả dụng với bác sĩ/kỹ thuật viên |
| 3. Kiểm tra | Có biên, cạnh vỏ, khoảng cách đo thực, va chạm lấy mẫu, mặt cắt/chu vi, khóa xuất lỗi, người kiểm tra/nhật ký | Tự giao toàn bề mặt, kiểm giao tam giác và giữa hai mảnh, độ dày nhỏ nhất, áp lực, độ bền, xác thực người duyệt |
| 4. Mốc + giai đoạn | Ba mốc vùng, vùng nâng cục bộ; cơ bản/nâng cao; giai đoạn là hồ sơ | Nhận diện mốc giải phẫu, đo góc khớp, quy tắc điều trị được kiểm chứng. Chưa mặc định Cấp/Chính thức tự đổi độ ôm |
| 5. Mở rộng | Có vỏ hai mảnh với khe mở, không có chi tiết đai/lỗ/bo | Thumb spica, từng ngón, khuỷu gập và retopology tự động |
| 6. Kiểm chứng | Chưa thực hiện | Kế hoạch kiểm chứng có người phụ trách lâm sàng, dữ liệu vật liệu/in và đánh giá phù hợp mục tiêu sử dụng |

## Những điểm cần sửa trong lộ trình gốc

- “Form” và “parametric” là hai yêu cầu khác nhau. OBJ quad phục vụ chuyển sang T-Spline; JSON + script tạo User Parameters. Tham số mới chỉ thay hình học khi đã liên kết với feature. V3 có ví dụ liên kết `sf_thickness` với Thicken, chưa tự tái tạo Form.
- Không lấy khoảng chừa danh nghĩa làm bản đồ khoảng cách thực. V3 tính/lưu riêng hai đại lượng. Khoảng cách không dấu không chứng minh không xuyên nhau.
- Không nội suy mặt cắt thiếu như thể đã đo được giải phẫu. V3 chỉ tính chu vi khi có đúng một vòng kín; đối chiếu yêu cầu cùng mặt phẳng thước dây.
- Không dùng nhãn “an toàn” cho việc chỉ kiểm cạnh kín. Checklist tách kiểm hình học, lấy mẫu, chưa nhập và chưa kiểm định.
- “Sai số dưới 0,5 mm”, “chu vi lệch 3 mm” là mục tiêu/ngưỡng nghiên cứu cần được chứng minh phù hợp; không thể coi là giới hạn lâm sàng phổ quát. V3 chỉ dùng 3 mm như ngưỡng đối chiếu có thể sửa.
- Không tự mặc định đổi giai đoạn là không cần quét lại. AAOS mô tả việc giảm sưng có thể khiến cast rộng và cần thay; việc có dùng lại scan phải dựa vào hình dạng hiện tại và đánh giá lâm sàng, chưa được v3 tự quyết định.
- Vỏ hai mảnh là bước nền để phát triển sản phẩm dạng cast; hình học hai mảnh đơn thuần chưa phải một hệ cast hoàn chỉnh có cơ cấu đóng, đệm và độ bền đã kiểm chứng.

## Quy tắc xuất v3

Khóa khi vùng chọn rỗng/nhiều mảnh/hở bất thường/lỗi cạnh, hướng offset quay vào trục theo phép kiểm hiện có, tìm thấy điểm quét trong thành vỏ ở mẫu kiểm, chu vi đã nhập lệch ngưỡng hoặc không đo được; cũng khóa khi kết quả đã cũ. Còn thiếu người kiểm tra/ô kiểm tra sẽ không ghi gói.

Chưa nhập chu vi được ghi `NOT_ENTERED`; vẫn cho xuất bản nghiên cứu sau kiểm thủ công. Không đánh dấu đó là đạt lâm sàng. Giới hạn quads chỉ khóa OBJ, không tự chặn các đầu ra hình học hợp lệ khác. Các kiểm tra toàn bề mặt/áp lực/độ bền còn `NOT_VALIDATED`.

## Lưu ý về thuật toán va chạm

Chỉ dùng vỏ tạo ra đã kín để kiểm bên trong, không đóng mesh quét hở. Signed distance sàng lọc các ứng viên sâu hơn 0,05 mm; xác minh bằng winding solid angle vì pseudonormal có thể sai dấu gần góc lõm. Có lấy mẫu tối đa và ngân sách tính toán. Không thấy ứng viên sau kiểm chỉ có nghĩa chưa phát hiện ở mẫu kiểm, không phải chứng minh không có giao nhau.

## Nguồn chính đã đối chiếu

- PyVista: [compute_implicit_distance](https://docs.pyvista.org/api/core/_autosummary/pyvista.datasetfilters.compute_implicit_distance) và [cảnh báo select_enclosed_points](https://docs.pyvista.org/api/core/_autosummary/pyvista.datasetfilters.select_enclosed_points).
- Autodesk: [UserParameters.add](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_UserParameters_add.htm), [ValueInput.createByString](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ValueInput_createByString.htm), [Scripts and Add-Ins](https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-MANAGE-SCRIPTS-ADD-INS.htm).
- PyInstaller: [Usage và đóng gói theo hệ điều hành](https://pyinstaller.org/en/stable/usage.html).
- AAOS: [Care of Casts and Splints](https://www.orthoinfo.org/recovery/care-of-casts-and-splints/).
- FDA: [Technical Considerations for Additive Manufactured Medical Devices](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/technical-considerations-additive-manufactured-medical-devices), nguồn tham khảo về kiểm thử/đặc tính sản phẩm in; không khẳng định app tuân thủ quy định của quốc gia nào.
