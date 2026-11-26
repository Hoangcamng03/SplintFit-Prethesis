# SplintFit Cast Prototype v4.0.1

**Tiến trình đến 26/11/2026:** [PROJECT_PROGRESS.md](docs/PROJECT_PROGRESS.md). Repository hiện là **Public** để giảng viên truy cập. Những đề xuất giao diện mới chưa được triển khai; phiên bản phần mềm vẫn là v4.0.1.

Bản desktop Windows kế thừa SplintFit v3.2, bổ sung nẹp hai mảnh có lỗ thoáng và lưới quad dành cho Fusion Form.

**Bắt đầu:** mở BAT_DAU_O_DAY.md. Repository không chứa mesh/ảnh/HTML nhúng hình học. Mở app và dùng mẫu mô phỏng tạo từ code, hoặc chạy python build_demo.py --output demo_export rồi mở demo_export/XEM_MAU_3D.html. Muốn chạy app: nhấp đúp START_WINDOWS.bat.

## Đã triển khai

- Nạp STL/OBJ/PLY, chọn đơn vị và ba mốc vùng nẹp.
- Fit bề mặt từ mặt cắt thực của scan; giữ hệ tọa độ chung với scan.
- Tạo vỏ hai mảnh, khe tháo lắp, lỗ oval xuyên thành và ba dải có khe luồn đai.
- Đường khuyết chữ U ở đầu bàn tay: chỉnh độ sâu, độ rộng và góc; không tự nhận diện giải phẫu.
- Xuất STL riêng từng mảnh; OBJ quad nền đơn giản và OBJ quad đã có lỗ.
- Lưu/mở JSON, undo, vô hiệu hóa kết quả khi đổi thông số; tương thích dự án v3.
- Trang xem 3D offline đi kèm từng gói xuất, không cần cài Python để xem.
- Mẫu mô phỏng cẳng tay–cổ tay–bàn tay để thử toàn bộ luồng.

## Chưa kiểm chứng hoặc chưa triển khai

Chưa thử trực tiếp Windows/Fusion, chưa tạo native Form hoặc F3D tự động. OBJ là đầu vào để thử Convert sang T-Spline; smoothing có thể thay đổi độ vừa và lỗ. Script Fusion hiện chỉ nhập User Parameters, chưa liên kết hoặc tự dựng feature.

Chưa tự bo mép, chưa có đai vật lý, chưa có nhánh ôm ngón cái/spica và chưa sao chép chính xác hình sản phẩm tham khảo. Chưa kiểm tự giao đầy đủ, áp lực, độ bền hoặc sử dụng trên người.

Engine mới chỉ nhận vùng có mặt cắt một vòng kín, dạng hướng tâm. Vùng cong mạnh, tách ngón, nhiều contour hoặc thiếu dữ liệu sẽ cần thu vùng/quét bổ sung hoặc phương pháp khác. Khoảng chừa, độ dày và tỷ lệ lỗ là giá trị thử, không phải thông số điều trị.

## Kiểm tra

Đọc TEST_RESULTS.md. Chạy:

    python -m unittest discover -s tests -v

Không cần pytest. Lệnh tạo lại ví dụ không mở UI:

    python build_demo.py --output my_demo_export

Thư mục xuất phải mới để tránh ghi đè bản cũ.

## Mã nguồn

app.py: giao diện/worker; geometry.py: xử lý và xuất chung; cast_template.py: fit mặt cắt và dựng panel có lỗ; viewer.py + viewer_template.html: xem offline; measurements.py: mặt cắt đo; project_io.py: lưu/mở và xác minh dự án; tests: kiểm thử.

Phương pháp mới là triển khai thử nghiệm riêng dựa trên hướng scan–thiết kế–chế tạo đã tổng hợp, không phải tái lập chính xác phần mềm AutoMedPrint, ActivArmor hay thuật toán độc quyền.

Các tài liệu v3 được giữ trong history/v3_docs để truy vết. Xem FUSION_FORM.md cho bước tiếp theo.

## Lab notes và nguyên tắc lỗ

- docs/PERFORATION_DESIGN.md: quy tắc hiện tại, căn cứ nghiên cứu và phần chưa kiểm chứng.
- LAB_NOTES/README.md: nhật ký từng thay đổi.
- CONTRIBUTING.md và AGENTS.md: cách tạo note và commit source.
- CHANGELOG.md: thay đổi theo phiên bản.

V4.0.1 không đổi hình học mặc định của v4. Gói demo_export trong ZIP baseline được giữ như bằng chứng v4; thư mục này không có trong repository source. Tạo lại demo bằng app hoặc build_demo.py; các trường giải thích mới trong báo cáo chỉ xuất khi dựng lại bằng app hiện tại.

## Đánh giá luồng dự án và tính khả thi

Xem [docs/PROJECT_FEASIBILITY.md](docs/PROJECT_FEASIBILITY.md) cho đối chiếu lâm sàng, bằng chứng quốc tế, Fusion và các trường hợp lỗi.
