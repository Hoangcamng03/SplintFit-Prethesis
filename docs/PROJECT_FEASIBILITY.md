# Đánh giá luồng và tính khả thi — 24/11/2026

## Kết luận

Khả thi để phát triển một quy trình bán tự động tạo prototype nẹp cổ tay–cẳng tay cá thể hóa, có chỉnh tay trong Fusion. Chưa đủ bằng chứng cho nẹp điều trị gãy/trật khớp hoặc tự động xử lý mọi scan. Không có căn cứ đặt xác suất thành công hoặc cam kết “nẹp hoàn hảo”.
Sản phẩm nghiên cứu nên được đánh giá theo mục đích sử dụng, dữ liệu đầu vào, phép kiểm và kết quả vật lý. Các đánh giá mức độ bên dưới là nhận định kỹ thuật từ mã và nguồn tham khảo, không phải xác suất thống kê.

## Định nghĩa và phạm vi

WHO defines an orthosis as an externally applied device that supports or modifies neuromusculoskeletal structure/function [1]. Vì vậy, hình giống nẹp mới đáp ứng một phần yêu cầu. Chức năng hỗ trợ/bất động, giao diện da–đệm, khả năng tháo lắp và chế tạo đều phải có căn cứ.
Tên mục tiêu giai đoạn này: quy trình bán tự động tạo prototype nẹp cổ tay–cẳng tay hai mảnh, có kiểm hình học và hiệu chỉnh CAD. Tên “cast 3D” hoặc số lỗ không tự chứng minh tác dụng điều trị.

## Mạch dự án và trạng thái

| Công đoạn | Có trong source | Phần cần bổ sung/kiểm thực tế |
|---|---|---|
| Xác định nhu cầu | Có trường hồ sơ/tư thế | Một intended use cụ thể; người phụ trách chuyên môn xác định vùng giữ và phép thử |
| Quét và tỷ lệ | Nhập OBJ/PLY/STL, đổi đơn vị, đo tham chiếu | Protocol KIRI, dữ liệu lặp và chuẩn đối chiếu độc lập |
| Chọn vùng | Ba mốc và ROI | Landmark giải phẫu; ba mốc không phải kỹ thuật tạo khuôn ba điểm |
| Tạo nẹp | Fit mặt cắt, offset, vỏ hai mảnh, lỗ/khe đai | Chỉ một vòng hướng tâm; chưa nhận mọi bàn tay/ngón cái hoặc tư thế cong |
| Kiểm hình học | Topology, khoảng cách/va chạm lấy mẫu, chu vi | Tự giao toàn bộ, vách nhỏ nhất, độ dày thực, vùng loại trừ lỗ theo giải phẫu |
| Fusion | Hai loại OBJ quad, tham chiếu, JSON và script tham số | Thử Convert/Edit Form/Finish Form/Thicken thật và đo sai lệch sau chỉnh |
| Chế tạo | STL xuất riêng từng mảnh | Máy/vật liệu/hướng in, xử lý mép, đệm–đai, đo mẫu sau in |
| Đánh giá | Test phần mềm và lab notes | Độ cứng/độ bền, hạn chế chuyển động trên mô hình, độ vừa/khả dụng theo phạm vi được duyệt |

Luồng mục tiêu: yêu cầu chuyên môn → scan có tỷ lệ → kiểm ROI → thiết kế → kiểm hình học → hiệu chỉnh Fusion → kiểm lại → slicer/in → hoàn thiện → đánh giá vật lý. Nếu một bước thất bại, trở lại bước tạo ra lỗi; không dùng hình đẹp để bỏ qua điều kiện chuyển tiếp.

## Bằng chứng thế giới và giới hạn suy luận

Servi et al. (2024) report a seven-step scan-to-two-piece orthosis workflow tested on 20 scans [2]. This supports engineering feasibility; their abstract does not validate this implementation or establish clinical performance for our prototype.
Guebeli et al. (2024) studied 39 selected fracture patients using DLP photopolymer splints versus fiberglass casts, reporting similar outcomes with more minor complications in the printed group [3]. This does not validate FDM PLA/PETG, different closures or our scan/design workflow.
Buonamici et al. (2020) offer a reference-pattern approach with structural/functional constraints [4]. Our grid pattern is a simpler rule-based design, not a reproduction of their optimized reference.

| Mục tiêu | Đánh giá kỹ thuật hiện tại |
|---|---|
| Tái lập mẫu tổng hợp và xuất vỏ | Đã có bằng chứng phần mềm; còn thử Windows/in |
| Nẹp theo một scan thật phù hợp miền thuật toán | Khả quan có điều kiện; chưa có dữ liệu người dùng để xác minh |
| Chỉnh dáng trong Fusion Form | Có đường kỹ thuật, chưa thử trực tiếp |
| Mọi scan bàn tay/ngón cái đều tự ra mẫu giống ảnh | Chưa được hỗ trợ; có giới hạn topology/hình học nền |
| Tự chọn thiết kế điều trị từ chẩn đoán | Ngoài phạm vi hiện tại |

## Đối chiếu lâm sàng cần có

AO guidance links coverage, padding, swelling monitoring and motion control to the injury pattern [5,6]. A simple forearm cast does not adequately control pronation/supination [5]. Những điểm này cần chuyển thành yêu cầu thiết kế cùng người phụ trách; không suy ra từ mesh ngoài da.

Các câu hỏi phải chốt: cần giữ khớp nào và cho khớp nào cử động; tư thế khi quét; vùng cần bảo vệ/giảm tì; cách theo dõi phù và tiếp xúc; mục tiêu của hệ đóng. Khoảng chừa không phải bản đồ áp lực. Chiều dày và tỷ lệ lỗ mặc định chưa là chỉ định điều trị. Không dùng ngưỡng lệch chu vi 3 mm trong app làm chuẩn lâm sàng chung.
Đánh giá cơ học phải xét cả vỏ–đệm–đai. Thử phá hủy thực hiện trên gá/mô hình, không trên người đeo. Prototype người khỏe không chứng minh giữ nắn hoặc liền xương.

## Fusion: những gì có thể và chưa thể nói

Autodesk documents quad-mesh to T-Spline conversion and restrictions around intersecting geometry [7]. T-Spline Thicken is approximate and does not check self-intersection [8].
Đề xuất thử hai nhánh: OBJ nền để kéo dáng rồi hoàn thiện lỗ bằng CAD; OBJ perforated để thử giữ trực tiếp cấu trúc lỗ. Cả hai cần đo lại sau smoothing/chỉnh tay. JSON chỉ lưu dữ liệu/tham số; script hiện chỉ tạo/cập nhật User Parameters, chưa tự tái tạo Form hoặc liên kết feature. F3D được lưu trong Fusion sau khi mô hình được nhập/chỉnh.

## Các khả năng khi build và cách xử lý

| Tình huống | Hậu quả | Hành động cần thiết |
|---|---|---|
| Sai Python/venv hoặc thư viện Qt/VTK | App không mở/lỗi đồ họa | Dùng môi trường riêng, đúng requirements; giữ log và smoke test Windows |
| Scan sai đơn vị hoặc co giãn | Nẹp đẹp nhưng sai kích thước | Chuẩn tỷ lệ độc lập, không chỉ nhìn màn hình |
| Lỗ dữ liệu trong ROI | Dựng sai vùng giải phẫu | Chặn, thu vùng hoặc quét bổ sung; không biến thành lỗ thoáng |
| Nhiều contour/ngón cái phân nhánh | Không fit bằng engine hướng tâm | Giới hạn ROI hoặc thiết kế template/retopology khác; không giả báo thành công |
| Convert/Finish Form thất bại | Không có Form chỉnh được | Thử cage nền, kiểm topology và tự giao; lưu trường hợp thất bại |
| Form đổi độ vừa/vách lỗ | Mất tính tương ứng thiết kế | So sánh trước/sau và kiểm lại trên geometry cuối |
| Thicken hoặc vỏ tự giao | Solid/đường in không hợp lệ | Kiểm hình học, sửa vùng cong/độ dày; không coi watertight là đủ |
| In cong, tách lớp hoặc đai làm nứt khe | Mẫu không đạt dù STL hợp lệ | Đo mẫu in, kiểm vật liệu/hướng in/assembly, sửa thiết kế và thử lại |
| Nẹp quá cứng/khó tháo hoặc gây tì | Không đạt mục tiêu sử dụng | Đánh giá tổ hợp và yêu cầu chuyên môn; thay phiên bản và đo lại |
| Nhiều lần quét cho mẫu khác nhau | Quy trình chưa ổn định | Định lượng độ lặp; không tăng số tính năng trước khi tìm nguồn sai số |

## Điều kiện cho một sản phẩm đạt yêu cầu

Chốt tiêu chí trước khi thử: đúng tỷ lệ và đủ vùng dữ liệu; hình học cuối hợp lệ; độ vừa sau in trong giới hạn đã định; lắp/tháo và hệ đóng hoạt động; đáp ứng cơ học đạt yêu cầu tải đã thống nhất; giao diện da/đệm và khả dụng được đánh giá đúng phạm vi. Hiệu quả điều trị cần nghiên cứu và phê duyệt riêng.
Verification: làm đúng các yêu cầu kỹ thuật đã đặt. Validation: sản phẩm/quy trình đáp ứng mục đích sử dụng thực tế. 90 unit test chỉ hỗ trợ một phần verification phần mềm.

## Thứ tự làm tiếp

1. Trên Windows, đi hết một mẫu tổng hợp tới Fusion, lưu file F3D và kết quả Convert/Thicken, đo sai lệch trước/sau.
2. Kiểm một scan thật có đơn vị và số đo đối chứng; ghi nguồn, tư thế, vùng và các thất bại.
3. In mẫu đơn giản, hoàn thiện và lắp trên mô hình/gá; đo kích thước và tháo lắp.
4. Bổ sung metric vách/độ dày thực và protocol cơ học; so sánh mẫu lỗ có kiểm soát.
5. Chỉ mở rộng nghiên cứu độ vừa trên người hoặc điều trị sau khi chốt người hướng dẫn, thiết kế nghiên cứu và phạm vi được chấp thuận.

Không đặt lịch chắc chắn hoặc xác suất thành công khi chưa biết máy in, dữ liệu và nguồn lực chuyên môn. Đóng góp khả thi: quy trình có thể tái lập, giải thích được và có bằng chứng đo, thay vì chỉ tạo được giao diện hoặc STL.

## Nguồn đã đối chiếu

1. WHO, Standards for prosthetics and orthotics, Part 1: https://iris.who.int/bitstream/handle/10665/259209/9789241512480-part1-eng.pdf
2. Servi et al., 2024, institutional abstract: https://flore.unifi.it/handle/2158/1375712
3. Guebeli et al., 2024, PubMed abstract: https://pubmed.ncbi.nlm.nih.gov/37458129/
4. Buonamici et al., 2020: https://doi.org/10.14733/cadaps.2020.325-336
5. AO Surgery Reference: https://surgeryreference.aofoundation.org/orthopedic-trauma/adult-trauma/distal-forearm/complete-simple-articular-simple-metaphyseal-radial-fracture/nonoperative-treatment-cast
6. AO carpal cast technique: https://surgeryreference.aofoundation.org/orthopedic-trauma/adult-trauma/carpal-bones/basic-technique/immobilization-with-a-cast
7. Autodesk Convert: https://help.autodesk.com/cloudhelp/ENU/Fusion-Sculpt/files/GUID-05F58BC6-C2E8-4965-8CA8-E370CED415A5.htm
8. Autodesk Thicken: https://help.autodesk.com/cloudhelp/ENU/Fusion-Sculpt/files/GUID-55A3BEDB-5CE2-48C1-9148-DAF3CE9CE6E9.htm

Đây là đánh giá định hướng theo source hiện có và nguồn đã đọc, không phải systematic review, chứng nhận thiết bị hoặc kết quả thử lâm sàng của SplintFit.
