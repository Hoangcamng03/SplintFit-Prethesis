# Tiến trình SplintFit — cập nhật 26/11/2026

## Trạng thái hiện tại

Phiên bản phần mềm: **v4.0.1 prototype**. Repository: **Public**, đã kiểm bằng GitHub connector ngày 26/11/2026.
Dự án đang có prototype tạo hình và xuất dữ liệu; chưa hoàn tất chuỗi kiểm chứng Windows → Fusion → in → đánh giá vật lý.
Bản cập nhật này tổng hợp hồ sơ, không phải phiên bản thuật toán mới.

## Các mốc có bằng chứng

| Ngày sự kiện | Công việc | Bằng chứng và giới hạn |
|---|---|---|
| 20/11/2026 | Baseline v4: desktop Qt/PyVista, fit scan theo mặt cắt, nẹp hai mảnh có lỗ/khe đai, STL/OBJ/JSON và viewer offline | [LN-001](../LAB_NOTES/LN-20261123-001_v4-baseline-retrospective.md), ghi hồi cứu ngày 23/11; 83 test Python theo hồ sơ baseline; mẫu tổng hợp 24 lỗ, 12 khe đai. Không phải scan người thật hoặc mẫu in |
| 23/11/2026 | v4.0.1: làm rõ nguyên tắc lỗ và bổ sung quản lý lab note | [LN-002](../LAB_NOTES/LN-20261123-002_hole-pattern-and-versioning.md); 90/90 test Python trong Linux/Python 3.12.14; viewer qua Node harness, chưa phải trình duyệt thật |
| 24/11/2026 | Tạo repository Private, nhập source và tài liệu | [LN-003](../LAB_NOTES/LN-20261124-003_private-github-import.md); commit source `8ae667b8e5445b67ad6aab43d3f7f750d0dce218`. Không đưa scan/mesh/ảnh/HTML nhúng hình học vào lần nhập |
| 24/11/2026 | Đối chiếu tính khả thi, phạm vi lâm sàng và Fusion | [LN-004](../LAB_NOTES/LN-20261124-004_feasibility-and-clinical-scope.md), [báo cáo](PROJECT_FEASIBILITY.md); cập nhật tài liệu, không sửa engine |
| 26/11/2026 | Chuyển repository Public theo xác nhận của chủ dự án; tổng hợp tiến trình và yêu cầu mới | [LN-005](../LAB_NOTES/LN-20261126-005_progress-and-public-access.md); Public được connector xác nhận. Giao diện hướng dẫn mới chưa triển khai |

Các bản MVP trước v4 thuộc bối cảnh phát triển; bộ lab note hiện tại chưa đủ để khôi phục ngày và kết quả từng lần sửa. Không dựng thêm lịch sử thực nghiệm không có bằng chứng.

## Đã có, đã kiểm và còn thiếu

| Hạng mục | Trạng thái |
|---|---|
| Nhập STL/OBJ/PLY, đơn vị, ba mốc, lưu/mở dự án | Có trong source; chưa có báo cáo chạy Windows mới |
| Dựng vỏ theo mặt cắt, hai mảnh, lỗ và khe đai | Có; bằng chứng phần mềm trên dữ liệu tổng hợp |
| Lỗ thoáng | Có quy tắc, không ngẫu nhiên; chưa tối ưu/kiểm chứng cơ học |
| STL để xem/slicer và hai loại OBJ quad cho Fusion | Có xuất file; chưa xác nhận Convert/Edit Form/Finish Form/Thicken trực tiếp |
| Script Fusion | Nhập/cập nhật User Parameters; chưa tự dựng Form, nhập OBJ hoặc liên kết feature |
| Nẹp qua khuỷu gập, nhánh ngón cái/spica, tự nhận diện giải phẫu | Chưa hỗ trợ |
| Giao diện hướng dẫn cho người mới, chọn vùng bằng hình minh họa | Đã thảo luận yêu cầu; chưa triển khai bản mới |
| Độ chính xác trên scan thật, in và hoàn thiện đệm–đai | Chưa có kết quả được cung cấp trong hồ sơ |
| Độ bền, áp lực, chức năng bất động và hiệu quả lâm sàng | Chưa được kiểm chứng |

Không quy đổi bảng này thành phần trăm hoàn thành vì phạm vi thesis và tiêu chí nghiệm thu chưa chốt.

## Yêu cầu mới đã ghi nhận từ chủ dự án

- Pre-thesis báo cáo theo tiến độ thực tế; thesis cần sản phẩm hoàn thiện đầu ra. “Hoàn thiện” còn cần thống nhất tiêu chí với giảng viên.
- Có giảng viên hướng dẫn và khả năng dùng máy in/vật liệu của thầy/lab. Chưa xác nhận loại máy, vật liệu, lịch sử dụng hoặc thiết bị thử.
- Vướng mắc chính: chưa hiểu luồng và thông số, chưa có nền tảng kỹ thuật lâm sàng đủ để tự xác định yêu cầu điều trị.
- Mong muốn: app dễ hiểu, có hướng dẫn/test mẫu, giải thích từng thông số và chỉnh thủ công trong Fusion.
- Chưa chốt người dùng chính, người hỗ trợ lâm sàng, phạm vi template và bộ dữ liệu thử.

Đây là thông tin nhu cầu/nguồn lực do người dùng cung cấp, không phải kết quả kiểm chứng thiết bị.

## Luồng phát triển đề xuất, chưa triển khai đầy đủ

1. Thử mẫu tổng hợp hoặc thiết kế theo yêu cầu đã xác nhận.
2. Nạp scan, kiểm tỷ lệ và vùng dữ liệu.
3. Chọn template được hỗ trợ; giải thích và chặn template chưa hỗ trợ.
4. Chọn mốc/đường biên trực quan; xem trước vùng và chiều dài.
5. Nhập độ ôm/đệm/vỏ; tách nhóm cơ bản và nâng cao, giải thích đơn vị và nguồn giá trị.
6. Tạo và kiểm hình học; báo lỗi gắn với vùng cần sửa.
7. Xuất theo mục đích: lưu tiếp, xem 3D, chỉnh Fusion, chuẩn bị in thử.

Dữ liệu đo được, yêu cầu chuyên môn và thông số thiết kế phải được phân biệt. Không suy ra chỉ định từ điểm bấm “gãy/đau”, không gọi giá trị thử là mặc định điều trị.

## Các bước tiếp theo và điều kiện hoàn thành

| Thứ tự | Việc cần làm | Kết quả cần lưu |
|---|---|---|
| 1 | Chốt phạm vi và tiêu chí sản phẩm với giảng viên | Loại nẹp, người dùng, chức năng, phép đo và tiêu chí; xác nhận nguồn lực |
| 2 | Đi hết một ca mẫu trên Windows | Phiên bản, bước thao tác, lỗi, thời gian, gói xuất; lab note mới |
| 3 | Thử OBJ nền và/hoặc có lỗ trong Fusion | Kết quả Convert/Edit Form/Finish Form/Thicken, F3D và sai lệch trước/sau |
| 4 | Cải thiện hướng dẫn dựa trên ca mẫu và quan sát người dùng | Thay đổi UI thực tế, nhiệm vụ thử, lỗi thao tác và phản hồi |
| 5 | Kiểm scan thật có tỷ lệ và số đo đối chứng | Protocol, dữ liệu được phép dùng, sai lệch và độ lặp |
| 6 | In và kiểm trên mô hình/gá | Máy/vật liệu/hướng in, số đo sau in, hoàn thiện mép/đệm/đai |
| 7 | Đánh giá theo đề cương được thống nhất | Kết quả hình học, cơ học, khả dụng; phạm vi nghiên cứu trên người nếu được duyệt |

Không mặc định mở rộng qua khuỷu trước khi quy trình dưới khuỷu được xác minh.
