# Mở và chạy v3.2 trên Windows + VS Code

## 1. Chuẩn bị

Giải nén ZIP mới vào `D:\SplintFit_v3`. Mở VS Code → File → Open Folder → chọn thư mục chứa trực tiếp `app.py`, thường là `D:\SplintFit_v3\SplintFit_Form_MVP`.

Không chép đè vào thư mục đang chạy bản cũ. Giữ bản cũ và mesh/dự án để đối chiếu.

## 2. Cài môi trường

Cài extension Python của Microsoft trong VS Code. Terminal → New Terminal → chọn Command Prompt, chạy từng dòng:

```bat
cd /d D:\SplintFit_v3\SplintFit_Form_MVP
python --version
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Đổi đường dẫn dòng đầu nếu bạn giải nén nơi khác. `python --version` cần báo Python 3.11.x hoặc 3.12.x.

Ctrl+Shift+P → Python: Select Interpreter → chọn `.venv\Scripts\python.exe` của thư mục này.

## 3. Chạy

```bat
.venv\Scripts\python.exe app.py
```

App mở cửa sổ riêng. Mở `app.py` rồi F5 cũng chạy được bằng cấu hình kèm theo nếu Python Debugger của Microsoft đã có. Có thể nhấp đúp `START_WINDOWS.bat` để cài/chạy.

Hướng dẫn thao tác mới: đọc `BAT_DAU_O_DAY.md`; nút xanh luôn ở dải hướng dẫn phía trên.

## 4. Thử mẫu trước

1. Bước 1 → Thử với mẫu tổng hợp.
2. Bước 3 → Tạo / Cập nhật nẹp.
3. Bước 4 → xem báo cáo và ba mặt cắt tím. Bật Khoảng chừa để xem khoảng cách đo thực.
4. Bước 5 → nhập tên người kiểm tra, tích ô kiểm tra → Xuất mô hình 3D.
5. Xem `FUSION_FORM.md` để nhập OBJ và thông số sang Fusion.
6. Để thử bó bột hai mảnh: bước 3 → Kiểu nẹp → Nẹp hai mảnh → đặt khe mở dương → Tạo lại. Gói xuất có OBJ, STL riêng cho từng mảnh; `example_bivalve_export` có mẫu sẵn.
7. Để thử nhập file: chọn mm rồi nạp `sample_data/synthetic_forearm_mm.obj`. Đây là hình học tổng hợp; khi nạp theo đường file vẫn phải xác nhận kích thước/chọn mốc.

## 5. Dùng mesh KIRI

1. Chọn mm/cm/m trước khi nạp STL, OBJ, PLY dạng bề mặt. Nếu đổi đơn vị đã chọn, nạp lại file.
2. Chọn đúng mảnh quét; kiểm tra kích thước. A–B là khoảng cách thẳng, không phải chu vi. Nếu cần: chọn A–B, nhập số đo, bấm Hiệu chỉnh theo số đo, kiểm lại rồi xác nhận.
3. Chọn ba mốc vùng nẹp bằng nút tương ứng + chuột phải lên da; xác nhận vùng. Điểm thứ ba xác định mặt đặt, app chưa nhận diện mặt lòng/lưng tự động.
4. Chỉnh đệm, khoảng chừa, độ dày và bao phủ; các giá trị là đầu vào hình học nghiên cứu.
5. Bước 4: nếu có số đo thước dây, nhập chu vi tại đúng ba mặt phẳng tím. Để 0 khi chưa đo. Phải bấm Tạo / Cập nhật lại sau thay đổi. Khi đổi hai đầu/giới hạn/mảnh/tỷ lệ, chu vi cũ bị xóa vì mặt phẳng đã đổi.
6. Vòng hở/đa vòng không được tự nối. Nếu đã nhập số đo nhưng không đo được hoặc lệch ngưỡng: giữ xem trước, chặn xuất. Kiểm lại mặt phẳng, scale hoặc quét bổ sung.
7. Kiểm tra, nhập người kiểm tra và xuất. Xuất nghiên cứu không thay thế đánh giá lâm sàng.

## 6. Kiểm thử

Đóng app rồi chạy:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Hoặc nhấp đúp `CHECK_AND_TEST_WINDOWS.bat`. Thành công khi cuối kết quả có `OK`; không dùng kết quả đó làm chứng nhận an toàn cho nẹp.

## 7. Build `.exe` trên Windows

Nhấp đúp `BUILD_WINDOWS.bat`. Script cài PyInstaller, chạy kiểm thử, rồi đóng gói. Nếu thành công, đầu ra:

```text
dist\SplintFit\SplintFit.exe
```

Phải giữ/chuyển cả thư mục `dist\SplintFit`, bao gồm `_internal`. Không chỉ gửi file `.exe` đơn lẻ. Recipe chưa được chạy trực tiếp trên Windows trong môi trường phát triển; cần thử trên máy đích trước khi phân phối. Gói được giao hiện là mã nguồn, chưa phải bộ `.exe` Windows đã kiểm chứng.

## 8. Khi lỗi

- Lỗi trước khi có cửa sổ: chạy lệnh ở bước 3 trong Terminal và giữ nguyên traceback.
- Lỗi khi nạp mesh: ngay bước 1 → Xuất báo cáo lỗi nạp file. Không cần nạp thành công mới xuất được báo cáo.
- Lỗi khi dựng/xuất: bước 5 → Xuất báo cáo để kiểm tra lỗi.
- Log trên Windows: `%LOCALAPPDATA%\SplintFit\splintfit.log`.
- Gửi mesh thử đã ẩn thông tin nhận dạng nếu phù hợp, báo cáo, ảnh và traceback. Báo cáo có thể chứa mã ca/đường dẫn máy; không nhúng mesh.
- Lỗi `ModuleNotFoundError`: kiểm tra interpreter `.venv`, chạy lại cài requirements.
- Màn hình 3D trống/OpenGL: cần kiểm driver GPU và thông báo Terminal trên máy Windows. Các kiểm thử headless không kiểm được driver đó.
