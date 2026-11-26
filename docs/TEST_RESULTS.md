# Kết quả tái hiện — 26/11/2026

## Môi trường và mức bằng chứng

Linux, Python 3.12; Flask 3.1.2, PyVista 0.49.0, VTK 9.3.1, NumPy 2.3.5, SciPy 1.17.0. Các số dưới đây là quan sát của lần chạy, không phải cam kết hiệu năng trên Windows.

Baseline studio-v2 có 2 test API, chạy lại qua trong 2,055 giây. Bản rà soát thêm 8 test hồi quy cho scale/kiểu dữ liệu, xác nhận vùng, build thất bại, xuất cũ, mất tam giác và đường dẫn tải file. Tổng 10 test Python qua trong 11,552 giây ở lần cuối; xem verification/unittest_20261126.txt cho lần kiểm cuối. Node workflow harness qua; JavaScript qua kiểm cú pháp. Không cộng 90 test của bản Qt/main vào số test Studio vì bộ test/kiến trúc khác nhau.

## Dữ liệu công khai

- Nguồn và quyền dùng: [UW GRAIL](https://grail.cs.washington.edu/data/scans/); nghiên cứu, phi thương mại, ghi công tác giả. Xem TEST_PROTOCOL.md.
- arms-obj.zip SHA-256: 8173ea5ed4a93a4ee358924ee84a1a3d8d7b7ad727a38e508dda776ea0487fe3.
- 001.obj SHA-256: 0984b05e1980e4b5fcd465f50e97b0c496db516c2c672ff069f4ec307ef72730.
- Sau đọc/clean: 48.215 đỉnh, 94.795 tam giác, 1 thành phần, 1.677 cạnh biên hở. Không vá biên hoặc thiếu dữ liệu.
- Gợi ý tự động khoảng 536,5 mm; chọn thủ công ROI 206 mm, giữ tọa độ nguồn. Chỉ kiểm một scan ở một tư thế; ba cấu hình không phải ba người.

## Kết quả luồng API + hình học + file

| Cấu hình thử | Chiều dài | Lỗ thoáng / khe đai | Tam giác hai vỏ | Mặt OBJ nền / có lỗ (tổng hai mảnh) | Thời gian dựng lần đầu |
|---|---|---|---|---|---|
| B: chừa 1,5 + đệm 0,5 mm | 206,0 mm | 26 / 12 | 9.216 | 840 / 1.888 | 2,615 s |
| A: chừa 2,5 + đệm 1,0 mm | 206,0 mm | 26 / 12 | 9.216 | 840 / 1.888 | 2,710 s |
| C: chừa 1,3 + đệm 0 mm, không lỗ thoáng | 206,0 mm | 0 / 12 | 6.720 | 840 / 1.472 | 2,722 s |

Cả ba: nạp → dựng → xuất Fusion 5 mesh → xuất đầy đủ → tải từng file/ZIP → đọc lại qua. Cả 4 OBJ của mỗi gói có mặt 4 đỉnh; hai STL đọc lại kín theo cạnh, không cạnh non-manifold/mặt suy biến. Bounds scan tham chiếu giữ trong dung sai số .001 đơn vị thử. Không phát hiện điểm scan trong thành vỏ tại phép lấy mẫu; không chứng minh hết mọi giao nhau.

## Phát hiện quan trọng về khoảng chừa

| Cấu hình | Khoảng chừa nhỏ nhất danh nghĩa | Khoảng cách không dấu nhỏ nhất tại mẫu kiểm |
|---|---|---|
| B | 2,0 mm | 0,778 mm |
| A | 3,5 mm | 2,044 mm |
| C | 1,3 mm | 0,081 mm |

Khoảng dịch danh nghĩa tại đỉnh không bảo đảm khoảng cách nhỏ nhất của toàn bề mặt. Cấu hình C tiến rất gần scan dù không phát hiện va chạm tại mẫu. Vì vậy không gọi ba mẫu này “vừa/an toàn”, không lấy thông số này làm chỉ định. Giao diện được bổ sung khoảng cách lấy mẫu tách riêng với khoảng chừa danh nghĩa. Cần nghiên cứu độ chính xác mặt cong/mật độ lưới và kiểm hình học đầy đủ trước khi dùng ngoài prototype.

Thử âm: xóa một tam giác trong ROI → HTTP 422 “Vùng scan thiếu dữ liệu hoặc có cạnh lỗi; không tự vá lỗ trên vùng tiếp xúc da.” Mô hình trước đó bị vô hiệu hóa.

Đã kiểm thêm HTTP thật trên server 127.0.0.1:8766: health v2.1.0-research → upload multipart UW001 → build → export → tải ZIP 5 file đều HTTP 200. Xem verification/public_scan_summary_20261126.json.

## Những gì chưa thử

- Trình duyệt của phiên không truy cập được server 127.0.0.1 của môi trường thực thi; chưa kiểm WebGL, bố cục hoặc chọn thư mục qua thao tác trình duyệt. Không dùng Node harness thay bằng chứng GUI.
- Launcher/hộp thoại thư mục trên Windows; tương thích mọi trình duyệt.
- Autodesk Fusion: chưa Convert/Edit Form/Finish Form/Thicken thật, chưa có F3D.
- Slicer, in vật lý, đệm/đai, sai số vật lý, độ bền, áp lực và điều trị.
- Chưa đủ dữ liệu đánh giá độ lặp giữa nhiều scan/người, thiếu thước đo độc lập, chưa kiểm tư thế khuỷu gập.

Kết luận: **luồng phần mềm tới xuất/đọc lại file đã qua trên ca thử; toàn quy trình CAD–chế tạo–lâm sàng chưa được xác nhận**.
