# SplintFit Studio v2.1 — prototype nghiên cứu

Web app cục bộ giúp tạo mẫu nẹp cổ tay–cẳng tay dưới khuỷu từ scan ngoài da. Luồng: **Nạp và kiểm tỷ lệ → chọn vùng → thông số thử → kiểm hình học → xuất OBJ/STL → chỉnh trong Fusion → in thử**.

Bản này rà soát từ `studio-v2` tại `fc89a8d`, giữ kiến trúc Flask + Three.js và engine mặt cắt của agent trước. Nhánh `main` là prototype Qt v4.0.1 có lịch sử riêng; không nhập đè hai lịch sử hoặc cộng số test của hai app.

## Bắt đầu trên Windows

1. Cài Python **3.12 64-bit**. Tải/giải nén nhánh này vào thư mục mới.
2. Nhấp đúp **START_STUDIO.bat**. Lần đầu cần Internet để cài requirements; giữ cửa sổ dòng lệnh.
3. Launcher đợi server sẵn sàng rồi mở trình duyệt tại **http://127.0.0.1:8765**. Phần 3D tải Three.js từ CDN.
4. Bấm **Mẫu cẳng tay – bàn tay**, sang bước 2, xem và xác nhận vùng, giữ bộ thử B/biên thẳng rồi tạo mẫu.
5. Đọc [hướng dẫn cho người mới](frontend/guide.html) hoặc mở liên kết Hướng dẫn trong app. Ctrl+C ở cửa sổ dòng lệnh để dừng server.

Chưa kiểm trực tiếp launcher Windows/GUI WebGL tại môi trường Linux; xem [kết quả thực tế](docs/TEST_RESULTS.md).

## Đã thay đổi trong bản rà soát

- Đổi nhãn “đang sưng/ổn định/ôm sát” thành **bộ thử A/B/C**, hiển thị số và tổng đệm + khoảng chừa. Độ dày không được gắn nhãn đã chứng minh độ cứng.
- “Safe-Zone” được mô tả là **gợi ý hình học lấy mẫu**, không tự xác định giải phẫu hoặc bảo đảm an toàn. Có cảnh báo vùng dự phòng và nút đảo hướng hai đầu.
- Xác nhận tỷ lệ/vùng; đổi đơn vị cần nạp lại, thay mốc cần xác nhận lại. Mặc định khuyết chữ U = 0, chỉ đặt khi kiểm được vị trí.
- Đổi thông số xóa kết quả/xuất cũ. API gắn build ID và đối chiếu thông số; build thất bại hoặc đổi mảnh xóa cache kết quả trước.
- Hiển thị **khoảng chừa danh nghĩa** và **khoảng cách không dấu lấy mẫu** riêng. Đã quan sát khoảng cách thực tại mẫu kiểm thấp hơn danh nghĩa đáng kể.
- Giữ xuất Fusion gọn: hai OBJ nền, hai OBJ có lỗ và scan STL tham chiếu cho hai mảnh; tùy chọn xuất đầy đủ có STL vỏ và báo cáo. OBJ không phải file F3D, kiểm tứ giác chưa bảo đảm Convert thành công.
- Thêm requirements, launcher môi trường riêng và hướng dẫn giải thích từng thông số.

## Kiểm thử và dữ liệu

- Baseline Studio: 2 test API; bản rà soát: **10 test Python** và **Node workflow harness**. Chi tiết và giới hạn ở [TEST_RESULTS](docs/TEST_RESULTS.md).
- Tìm và chạy scan **001.obj của UW GRAIL**, không dùng mô hình tự sinh thay thế scan: ba cấu hình, xuất hai loại gói, tải/đọc lại OBJ/STL/ZIP; thử mất một tam giác trong ROI bị chặn.
- Source/quyền dùng/hash/cách tái hiện: [TEST_PROTOCOL](docs/TEST_PROTOCOL.md). Dữ liệu nguồn chỉ được dùng nghiên cứu phi thương mại, có ghi công; scan và mesh dẫn xuất không được đưa lên GitHub trong lần cập nhật này.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node tests/test_frontend_workflow.cjs
.\.venv\Scripts\python.exe tools/check_public_scan.py --data-dir D:\SplintFit_Research\UW001
```

## Giới hạn cần giữ khi báo cáo thesis

Engine nhận vùng có mặt cắt một vòng kín hướng tâm. Chưa hỗ trợ khuỷu gập/nhánh ngón cái, tự suy ra chỉ định, độ vững gãy, tư thế điều trị hoặc tự nắn scan. Không tự vá dữ liệu thiếu.

Kín theo cạnh, không thấy va chạm lấy mẫu hoặc có toàn mặt tứ giác **không chứng minh** độ vừa, độ bền, áp lực hay an toàn điều trị. Scan công khai không có số đo đối chứng người thật. Chưa thử trực tiếp Fusion, slicing hoặc in vật lý. Trình duyệt xem trước trong phiên không kết nối được server cục bộ nên GUI chưa được xác nhận.

## Nhật ký

- [LN-20261126-006](LAB_NOTES/LN-20261126-006_verified-studio-workflow.md): thay đổi, kết quả mới và giới hạn.
- [LABNOTE.md](LABNOTE.md): lịch sử agent trước được giữ nguyên; phần đính chính ở đầu phân biệt tuyên bố thiết kế với kết quả kiểm chứng.
