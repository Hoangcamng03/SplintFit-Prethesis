# Chỉnh nẹp trong Autodesk Fusion Form

## Điều đã có và điều cần kiểm

Gói đã chứa hình học OBJ/STL thực. Chưa chạy trực tiếp Autodesk Fusion trong môi trường phát triển.
Không có F3D native tạo tự động. Chuyển OBJ sang T-Spline và Finish Form có thể thất bại hoặc làm đổi độ vừa.

## A. Thử mẫu đã có lỗ trước

1. Mở Fusion > tạo một Design mới, đặt đơn vị tài liệu mm.
2. Preferences > Mesh: nếu có tùy chọn Triangulate mesh polygons, tắt để giữ mặt tứ giác.
3. Vào Create Form trong Design. Dùng Insert Mesh theo môi trường/phiên bản Fusion.
4. Chọn splint_form_perforated_piece_1_quad.obj. Đơn vị import Millimeter.
5. Giữ nguyên vị trí nhập. Không Center hoặc Move to Ground riêng từng file: chúng cần cùng hệ tọa độ với scan.
6. Trong Form, tìm Convert (Modify hoặc Utilities tùy giao diện). Selection Filter: Mesh Body. Chọn Quad Mesh to T-Splines.
7. Nếu thành công: chọn Edit Form, kéo điểm/cạnh/mặt ở mức nhỏ, xem lại cùng scan_reference_mm.stl.
8. Thử mảnh 2 tương tự. Không nhập đồng thời hai phiên bản nền và perforated rồi tạo hai lớp trùng nhau.
9. Nếu chuyển đổi báo lỗi: dùng Repair Body để xác định lỗi. Nếu vẫn lỗi, chuyển sang nhánh B; giữ file lỗi và ảnh thông báo để kiểm tiếp.
10. Finish Form. Mặt này là mặt trong hở, chưa phải solid đã có độ dày.
11. Trong Surface, dùng Thicken hướng ra ngoài với độ dày đã chọn. Kiểm chiều offset trên mô hình, không dựa riêng dấu +/−.
12. Thêm fillet/bo mép phù hợp, hoàn thiện vị trí đai và kiểm lại từng lỗ. Kiểm bề mặt tự giao hoặc quá mỏng sau chỉnh.
13. Lưu As trong Fusion để tạo dự án F3D. Xuất STL của các solid cuối cùng cho slicer.

Quan trọng: OBJ mặt trong đã có khoảng dành cho đệm + độ chừa + nâng cục bộ. Không offset lại các giá trị đó.
T-Spline smoothing làm thay đổi bề mặt và đường lỗ; phải đối chiếu với inner_piece_*_reference_mm.stl và scan.
Không dùng Thicken trong Form như một phép bảo đảm độ dày chính xác. Tài liệu Autodesk nêu công cụ này xấp xỉ và không tự kiểm tự giao.

## B. Nếu ưu tiên kéo chỉnh dáng dễ hơn

Nhập splint_form_piece_1_quad.obj và ...piece_2_quad.obj thay cho phiên bản perforated.
Đây là mặt nền có lưới đều hơn, không có lỗ thoáng hoặc khe đai, vẫn có biên và đường khuyết theo thiết kế.
Convert > Edit Form > Finish Form > Surface Thicken.
Sau đó tạo lỗ và chi tiết đai bằng các feature CAD trong Fusion. Bản này không tự giữ các lỗ của STL khi bạn đổi dáng; cần dựng/điều chỉnh lỗ trên hình học cuối.

## C. Script nhập thông số

Mở Utilities > Scripts and Add-Ins theo phiên bản Fusion. Thêm/chạy thư mục fusion/SplintFitImport.
Chọn fusion_user_parameters.json trong gói xuất.
Script chỉ tạo/cập nhật User Parameters. Muốn điều khiển feature, tự liên kết biểu thức, ví dụ sf_thickness với Thicken.
Script KHÔNG tạo Form từ JSON, KHÔNG nhập OBJ và KHÔNG tự khôi phục mẫu nẹp từ các tham số.

## D. Nguồn chính thức đã đối chiếu

- Import and convert mesh bodies to T-splines:
  https://help.autodesk.com/cloudhelp/ENU/Fusion-Sculpt/files/GUID-F8CFD835-9035-41F6-A428-F9D13900FD96.htm
- Convert reference:
  https://help.autodesk.com/cloudhelp/ENU/Fusion-Sculpt/files/GUID-05F58BC6-C2E8-4965-8CA8-E370CED415A5.htm
- Thicken or shell a T-Spline:
  https://help.autodesk.com/view/fusion360/ENU/?contextId=FORM-THICKEN-CMD
- Insert Mesh (đơn vị và vị trí):
  https://help.autodesk.com/cloudhelp/ENU/Fusion-Mesh/files/MESH-INSERT-MESH.htm

Mốc kiểm tài liệu: 20/11/2026. Tên nhóm công cụ có thể khác theo phiên bản.
