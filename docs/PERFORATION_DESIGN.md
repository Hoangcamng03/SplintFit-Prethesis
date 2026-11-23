# Quy tắc tạo lỗ trong SplintFit

## Kết luận về bản hiện tại

Mẫu lỗ là hình học có quy tắc, lặp lại được với cùng đầu vào. Nó chưa phải kết quả tối ưu hóa cơ học hay thiết kế được kiểm định lâm sàng. Hình dạng hữu cơ hoặc giống Voronoi trong ảnh thương mại không đủ để suy ra cách tạo hoặc mức độ tối ưu của sản phẩm.

## Những gì code đang làm

Nguồn trực tiếp: cast_template.py, hàm _tiles và build_piece.

| Quy tắc | Triển khai | Giới hạn |
|---|---|---|
| Chia vùng thành ô | Số hàng/cột dựa trên chiều dài vùng, góc ôm, bán kính trung vị và hole_pitch_mm; tối thiểu 4 cột/6 hàng | Pitch là mục tiêu danh nghĩa, không bảo đảm mọi khoảng cách trên mặt cong bằng giá trị mm này |
| Chừa hai đầu | Không đặt lỗ thoáng ở hàng đầu và cuối | Chưa đo mép còn lại nhỏ nhất theo mm |
| Chừa mép khe mở | Không đặt lỗ thoáng ở cột đầu và cuối | Các khe đai riêng vẫn xuất hiện ở cột này |
| Dải dành cho đai | Chọn ba hàng gần 22%, 50%, 78% chiều dài lưới; không đặt lỗ thoáng trong các hàng đó | Chỉ là bố trí vật liệu hình học; chưa chứng minh dải chịu được lực siết |
| Khe luồn đai | Oval tại hai mép của các hàng đai; bán trục theo tỷ lệ 0,30 và 0,62 của nửa ô | Chưa mô phỏng đai, mép khe hoặc tải đứt |
| Lỗ thoáng | Vòng 16 đỉnh tạo oval trong miền tham số, ánh xạ lên bề mặt fitted scan | Hình dạng/kích thước thực đổi theo vị trí; không phải oval giải tích giữ đường kính cố định |
| Tỷ lệ kích thước | hole_ratio là tỷ lệ theo hai chiều của ô tham số | 0,48 không nghĩa là 48% diện tích toàn nẹp bị bỏ |

Trong một ô phẳng lý tưởng, oval trơn có tỷ phần diện tích gần pi*r^2/4. Với r=0,48 là khoảng 18,1% của riêng ô đó; vòng đa giác 16 đỉnh hơi khác. Đây chỉ là minh họa toán học, không phải tỷ lệ rỗng đo được trên sản phẩm. Dải đai, ô đặc, khe và biến dạng mặt cong làm tỷ lệ toàn nẹp khác.

V4.0.1 bổ sung trạng thái RULE_BASED_GEOMETRY_NOT_MECHANICALLY_VALIDATED trong báo cáo. Bề rộng vách nhỏ nhất và tỷ lệ diện tích mở để null vì chưa đo; không thay null bằng số ước đoán.

## Nguyên tắc phát triển đề xuất — chưa triển khai đầy đủ

Thiết kế phải cân bằng thông thoáng, khối lượng, đường truyền lực, vùng tiếp xúc và khả năng sản xuất. Thay đường kính lỗ mà giữ nguyên pitch sẽ làm đổi phần vật liệu còn lại; không đánh giá chỉ bằng số lỗ.

Các ràng buộc nên bổ sung gồm: bề rộng vách nhỏ nhất trên hình học thực; khoảng cách lỗ–mép; vùng loại trừ theo mốc giải phẫu và mục đích sử dụng; đường vật liệu liên tục; hình học mép dễ hoàn thiện; giới hạn tương ứng máy/vật liệu/hướng in.
Phải kiểm lại sau khi chỉnh Form vì smoothing có thể làm đổi cả độ vừa và vách giữa lỗ. Không có ngưỡng kích thước chung được chốt trong tài liệu này.

Đề xuất thí nghiệm: giữ nguyên scan, vật liệu, độ dày, hướng in, đệm–đai và cách gá; so sánh vỏ không có lỗ thoáng với hai mức kích thước lỗ. Đo khối lượng, hình học sau in, lực–dịch chuyển và vị trí hỏng trên mô hình/gá. Nếu đánh giá thông thoáng thì cần phép đo riêng; diện tích mở không tự chứng minh giảm nhiệt/ẩm. Đây là đề xuất, chưa có kết quả thực nghiệm.

## Tài liệu nền và giới hạn bằng chứng

1. Buonamici et al. (2020), Automatic CAD Modeling of Ventilation Holes for 3D Printed Wrist Orthoses. DOI: https://doi.org/10.14733/cadaps.2020.325-336 . Full paper reviewed. The authors combine a reference pattern, structural/functional constraints and anatomical mapping, with numerical assessment. Their ABS-specific dimensions and loading assumptions are not adopted as universal defaults here. SplintFit does not reproduce their NX/optimization workflow.
2. Bandosz & Rychlik (2024), Design and Finite Element Analysis of a Custom Wrist Orthosis… DOI: https://doi.org/10.1007/978-3-031-56456-7_13 . Publisher abstract reviewed; full chapter not accessed. Describes topology-guided ventilation with medically required protection zones and geometry corrections after FEA. Not validation of our pattern.
3. Mian et al. (2023), Finite Element Analysis of Upper Limb Splint Designs and Materials for 3D Printing. DOI: https://doi.org/10.3390/polym15142993 . Publisher/abstract and indexed methods reviewed. Compares perforated and optimized designs under specific simulation assumptions; no universal best hole shape is inferred for this project.

Ngày kiểm nguồn: 23/11/2026. Không sao chép hình bài báo vào source. Các quy tắc mới ở trên là đề xuất kỹ thuật cần thử, không phải phác đồ điều trị.
