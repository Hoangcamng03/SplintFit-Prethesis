# Quy trình kiểm thử Studio v2.1

## Phạm vi

Kiểm phần mềm từ nạp dữ liệu tới xuất/đọc lại OBJ, STL và ZIP. Không thay thế thao tác trong Fusion, slicing, in vật lý, đo độ vừa hoặc đánh giá điều trị.

## 1. Cài và chạy

Python 3.12 64-bit. Windows: giải nén/clone nhánh này vào thư mục mới có START_STUDIO.bat, nhấp đúp file đó. Giữ cửa sổ Python để đọc lỗi; Ctrl+C để dừng. Chưa smoke-test launcher trên Windows tại môi trường phát triển Linux.

Lệnh tương đương trong PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch_studio.py
```

Mở http://127.0.0.1:8765. Phần 3D tải Three.js từ CDN; cần Internet khi tải frontend. Không mở server ra Internet.

## 2. Ca tổng hợp trên giao diện

1. Nạp mẫu tổng hợp; xác nhận tỷ lệ được đặt sẵn chỉ cho mẫu này.
2. Sang bước 2, xem hai vòng đầu–cuối; thử thu vùng, đảo hướng rồi xác nhận vùng.
3. Giữ bộ B, vỏ 3,2 mm và biên thẳng, bấm tạo.
4. Kiểm báo cáo, khoảng chừa danh nghĩa và khoảng cách lấy mẫu (hai giá trị khác nhau).
5. Xuất gói Fusion và gói đầy đủ; đọc lại file, giữ cùng tọa độ mm.
6. Quay lại bước 3 đổi chiều dày: kết quả/đường tải cũ phải biến mất; không thể xuất trước khi dựng lại.
7. Bỏ xác nhận tỷ lệ hoặc thay mốc: app yêu cầu kiểm lại. Đổi đơn vị cần nạp lại scan.

Ghi hệ điều hành, trình duyệt, phiên bản Python, mã commit, bước lỗi và thời gian. Các mục này chưa được coi là PASS chỉ vì API test qua.

## 3. Tái hiện bằng scan công khai

Nguồn: [University of Washington GRAIL — Arm Scan Data](https://grail.cs.washington.edu/data/scans/). Ghi công University of Washington Graphics and Imaging Laboratory; Brett Allen, Brian Curless, Zoran Popović, SIGGRAPH 2002. Trang nguồn cho phép nghiên cứu, không dùng thương mại hoặc trong sản phẩm bán khi chưa được phép. Không phát hành lại scan hoặc mesh dẫn xuất trong repository này.

```powershell
.\.venv\Scripts\python.exe tools/check_public_scan.py --data-dir D:\SplintFit_Research\UW001
```

Script tải arms-obj.zip, dùng 001.obj và ghi SHA-256 vào public_scan_report.json. Nó xử lý nguồn gốc, không dùng mẫu hình học tự sinh thay thế scan.

Quy ước thử: tọa độ nguồn được coi là mm (scale=1) dựa trên độ lớn và dữ liệu skeleton đi kèm; chưa có thước đối chứng của người được quét. Đây không phải xác nhận độ chính xác kích thước thực.

Scan gồm vai/cánh tay/cẳng tay/bàn tay nắm một ống. Thứ tự 001 mô tả khuỷu thẳng, xoay 0°, cổ tay gần trung tính; góc nguồn là xấp xỉ. Kiểm mục đích hình học, không gọi đây là ca gãy hay chứng minh bất động cổ tay.

- Vùng tự gợi ý dài khoảng 536,5 mm, có cả phần cánh tay trên; đó là giới hạn của PCA/lát cắt, không phải vùng giải phẫu được xác nhận.
- Ca thử thu đầu thứ nhất 330 mm và giữ đầu thứ hai ở floor(span) tương đương thanh trượt; khoảng giữa hai mốc là 206 mm. Vùng được chọn khi quan sát hình chiếu, không phải biên do chuyên gia lâm sàng duyệt.
- Dựng ba cấu hình nghiên cứu: có lỗ B (chừa 1,5 + đệm 0,5), có lỗ A (2,5 + 1), không lỗ C (1,3 + 0), vỏ 3,2 mm. Các giá trị là thử phần mềm.
- Mỗi ca xuất cả gói Fusion 5 mesh và gói đầy đủ. Kiểm 4 OBJ có mặt 4 đỉnh, STL từng mảnh kín theo cạnh, không non-manifold/mặt suy biến; đọc ZIP và so hash API file với file trên đĩa; đối chiếu bounds scan tham chiếu.
- Xóa một tam giác nguồn trong ROI rồi dựng lại: phải chặn với HTTP 422, không tự vá, không giữ mô hình cũ để xuất.

Kết quả định lượng ở [TEST_RESULTS.md](TEST_RESULTS.md). Gói sạch chỉ có mesh; chọn gói đầy đủ để lưu tham số và báo cáo truy vết.

## 4. Kiểm tự động và giới hạn

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node tests/test_frontend_workflow.cjs
```

Node harness chạy các hàm thật với bộ thích ứng DOM tối thiểu: kiểm trạng thái/xuất cũ/điều hướng, không chạy WebGL, bố cục hoặc hộp thoại chọn thư mục.

Sau đó còn cần thử GUI Windows, xuất thư mục thật và Fusion: Convert → Edit Form → Finish Form → Thicken, lưu F3D, đo lại hình học sau smoothing, rồi slicing/in và đo vật lý. Không báo “toàn quy trình chế tạo PASS” khi chưa có các bước này.
