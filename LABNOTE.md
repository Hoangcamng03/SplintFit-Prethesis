# NHẬT KÝ PHÁT TRIỂN DỰ ÁN (CAPSTONE LAB NOTEBOOK)
## Đề tài: SplintFit Studio — Hệ thống bán tự động thiết kế nẹp cổ tay–cẳng tay 3D cá thể hóa kết hợp Autodesk Fusion 360 (Form / T-Spline)

- **Lĩnh vực:** Kỹ thuật Y sinh (Biomedical Engineering) — Pre-thesis / Hướng tới Capstone Thesis
- **Mục tiêu tổng quát:** Xây dựng phần mềm trực quan, dễ thao tác cho cả **bác sĩ và kỹ thuật viên không chuyên CAD 3D**, giúp chuyển đổi trực tiếp mô hình quét 3D cánh tay (từ KIRI Engine) thành mẫu nẹp 2 mảnh cá thể hóa an toàn và xuất lưới tứ giác chuẩn (**All-Quad Mesh**) để hiệu chỉnh thủ công trong **Autodesk Fusion 360 (chế độ Form / T-Spline)** trước khi in 3D.
- **Chuỗi quy trình kỹ thuật (End-to-End Pipeline):**
  `Quét 3D tay (KIRI Engine) → SplintFit Studio (Xử lý & Tạo hình nẹp) → Autodesk Fusion 360 (Chỉnh Form & Bo mép) → In 3D kiểm thử`
- **Nguyên tắc an toàn cốt lõi:** **Không tự động vá lỗ quét (No Hole Filling)** trên vùng tiếp xúc da để tránh tạo ra bề mặt giả có thể gây cấn hoặc loét tỳ đè.

---

## Mốc 9 — 26/11/2026: Nhãn 3D trực tiếp cho 3 mốc tự động & Tự dựng sẵn nẹp 2 mảnh ngay khi nạp file

### 1. Bối cảnh & Quyết định kỹ thuật
Để người dùng nhìn thấy ngay lập tức hệ thống đã tự động xác định 3 mốc giải phẫu và giảm thao tác lặp lại:
- **Gắn nhãn chữ nổi trực tiếp trên mô hình 3D (`add_point_labels`):** Hiển thị rõ 3 điểm lớn kèm nhãn chữ trắng nổi bật (**`1. Đầu khuỷu`**, **`2. Cổ tay`**, **`3. Mặt nẹp`**) ngay trên cánh tay 3D; đẩy chấm tím ra ngoài bề mặt thêm `12 mm` để không bị khuất.
- **Tự động dựng sẵn nẹp 2 mảnh ngay khi nạp file (`chk_auto_build`, bật mặc định):** Ngay khi mở tệp `.stl`/`.obj`/`.ply` hoặc mẫu thử, phần mềm tự động khóa vùng an toàn, dựng luôn nẹp 2 mảnh lưới tổ ong và chuyển sang **Bước 2** để người dùng kéo 3 thanh trượt chỉnh lại vị trí rồi bấm **Cập nhật lại nẹp 3D** nếu muốn.

### 2. Trạng thái & Kết quả kiểm chứng
- **Kiểm thử tự động (`tests/test_desktop_app.py`):** PASS toàn luồng 5 bước với chế độ tự động dựng sẵn bật mặc định.
- Đã đồng bộ lên GitHub nhánh `studio-v2` và khởi chạy lại cửa sổ ứng dụng Desktop.

### 3. Hạn chế & Rủi ro đang mở
- Cần thực nghiệm mở trực tiếp `splint_form_piece_1_quad.obj` trong **Autodesk Fusion 360 (Create Form)**.

### 4. Bước tiếp theo cần làm ngay
1. Mở thử `Hand and Forearm - Full.stl` trong cửa sổ **SplintFit Studio Desktop** vừa bật để kiểm tra 3 nhãn 3D và nẹp 2 mảnh dựng tự động.
2. Xuất 5 file mesh và thử `Convert → Quad Mesh to T-Splines` trong Autodesk Fusion 360.

---

## Mốc 8 — 26/11/2026: Tinh chỉnh thẩm mỹ Desktop v3.1 (Sửa QSS, chiều sâu 3D & thẻ chọn 2 mảnh rõ ràng)

### 1. Bối cảnh & Quyết định kỹ thuật
Qua ảnh chụp thực tế bản Desktop v3.0 đầu tiên, phát hiện 3 lỗi hiển thị khiến giao diện kém trực quan hơn bản Web:
1. **Sai cú pháp selector QSS của Qt:** Dùng `.card`, `.presetCard`, `.stepPill` khiến Qt bỏ qua định dạng viền/nền của toàn bộ thẻ, nút Preset và ô tích (`QCheckBox` chưa tích bị trắng mờ không thấy ô vuông). → **Đã sửa toàn bộ sang cú pháp chuẩn Qt `[class="..."]`** và bổ sung viền rõ ràng cho `QCheckBox::indicator`.
2. **Lỗi thứ tự vẽ trong suốt 3D (Alpha-sorting):** Lớp da tay mờ bị vẽ đè lên vỏ nẹp đặc khiến nẹp trông nhạt và khó nhìn khối 3D. → **Đã bật `enable_depth_peeling(4)`** và đổi thứ tự vẽ vỏ nẹp đặc trước, lớp da mờ sau, tăng độ tương phản ánh sáng (`ambient`/`diffuse`/`specular`).
3. **Chọn cấu trúc 2 mảnh bị ẩn trong mục Nâng cao:** Đưa cặp thẻ **0. Cấu trúc nẹp (`Nẹp 2 mảnh tháo lắp` / `Nẹp 1 mảnh máng hở`)** lên ngay đầu Bước 3 (mặc định **2 mảnh**) để bác sĩ/kỹ thuật viên nhìn rõ ngay lập tức.

### 2. Trạng thái & Kết quả kiểm chứng
- **Kiểm thử tự động (`tests/test_desktop_app.py`):** PASS toàn luồng 5 bước, xác nhận mặc định tạo đủ **2 mảnh nẹp** và xuất đúng 5 file All-Quad cho Fusion 360 Form.
- Đã đồng bộ lên GitHub nhánh `studio-v2` và khởi chạy lại cửa sổ ứng dụng Desktop.

### 3. Hạn chế & Rủi ro đang mở
- Vẫn cần thực nghiệm mở `splint_form_piece_1_quad.obj` trong **Autodesk Fusion 360 (Create Form)** trên máy người dùng.

### 4. Bước tiếp theo cần làm ngay
1. Kiểm tra lại giao diện trực quan & 2 mảnh nẹp trên cửa sổ **SplintFit Studio Desktop** vừa mở.
2. Xuất 5 file mesh và thử `Convert → Quad Mesh to T-Splines` trong Fusion 360.

---

## Mốc 7 — 26/11/2026: Chuyển hoàn toàn sang Ứng dụng máy tính độc lập (Native Desktop App v3.0) & Dọn sạch phần Web

### 1. Bối cảnh & Quyết định kỹ thuật
Để người dùng vận hành phần mềm hoàn toàn tự nhiên như một ứng dụng máy tính Windows chuẩn (không cần mở trình duyệt, không cần chạy server web cục bộ, mở hộp thoại chọn thư mục Windows gốc 100% ổn định), toàn bộ giao diện **SplintFit Studio** đã được viết lại thành **ứng dụng Desktop gốc bằng PyQt6 + PyVistaQt**, giữ trọn vẹn thiết kế hiện đại và các tính năng đã kiểm chứng:
- **Giao diện sáng chuẩn y khoa (`desktop/theme.py`, `desktop/main_window.py`):** Quy trình 5 bước rõ ràng với đúng 1 nút hành động chính mỗi bước, thanh báo trạng thái gọn gàng không che tiêu đề.
- **Giữ nguyên 100% các nâng cấp cốt lõi:**
  - *Bước 1:* Mở trực tiếp file `.stl`/`.obj`/`.ply` bằng hộp thoại Windows gốc (`QFileDialog`) hoặc dùng mẫu giải phẫu cẳng tay–bàn tay.
  - *Bước 2:* Tự động khóa vùng an toàn (*Safe-Zone*) + 3 thanh trượt chỉnh trực tiếp vòng cắt 3D (*Đầu khuỷu*, *Đầu bàn tay*, *Xoay hướng tách 2 mảnh*).
  - *Bước 3:* 4 nhóm thẻ cấu hình lâm sàng cho Bác sĩ + mục mở rộng cho Kỹ thuật viên.
  - *Bước 4:* Khung 3D tương tác có thanh **Tách 2 mảnh**, chỉnh **Mờ chi**, bật/tắt **Lưới Quad (Fusion Form)** và bản đồ độ thoáng mặt trong.
  - *Bước 5:* Chọn nơi lưu trực tiếp bằng cửa sổ Windows gốc (`QFileDialog.getExistingDirectory`, tự nhớ thư mục qua `QSettings`) + 3 nút nhanh (`Desktop`, `Downloads`, `Documents`), xuất mặc định đúng 5 file mesh chuẩn cho Fusion 360 Form và mở thẳng thư mục bằng `explorer.exe`.
- **Dọn gọn toàn bộ phần không dùng:** Xóa hoàn toàn thư mục `backend/`, `frontend/` và bộ test web cũ `tests/test_studio_api.py`; thay bằng `desktop/` và `tests/test_desktop_app.py`.

### 2. Trạng thái & Kết quả kiểm chứng
- **Kiểm thử tự động ứng dụng Desktop (`tests/test_desktop_app.py`):** Đạt **1/1 toàn luồng 5 bước PASS (3,72 giây)** — xác minh nạp mẫu giải phẫu, trượt thanh Safe-Zone, dựng nẹp 2 mảnh lưới tổ ong, xuất đúng 5 tệp All-Quad (4 đỉnh/mặt) vào thư mục tùy chọn, và giữ nguyên tùy chọn xuất đầy đủ.
- **Kiểm chứng trên tệp tay thật `Hand and Forearm - Full.stl` (158.894 mặt):** Tự động nhận vùng an toàn cổ tay và dựng thành công nẹp 2 mảnh trực tiếp trong ứng dụng Desktop.

### 3. Hạn chế & Rủi ro đang mở
- Cần thực nghiệm trực tiếp bước chuyển đổi `Quad Mesh → T-Splines` trên phần mềm **Autodesk Fusion 360** từ gói xuất của bản Desktop v3.0.

### 4. Bước tiếp theo cần làm ngay
1. Người dùng nhấp đúp `START_STUDIO.bat` để mở trực tiếp **SplintFit Studio Desktop v3.0** trên Windows.
2. Xuất 5 file mesh ra Desktop/Documents và mở thử `splint_form_piece_1_quad.obj` trong **Autodesk Fusion 360 (Create Form)**.

---

## Mốc 6 — 26/11/2026: Chạy dạng cửa sổ ứng dụng máy tính độc lập & Dọn gọn mã nguồn

### 1. Bối cảnh & Quyết định kỹ thuật
Để người dùng không phải mở tab trình duyệt rườm rà hoặc gõ địa chỉ `127.0.0.1:8765`, đồng thời giữ thư mục dự án luôn sạch gọn, nhóm đã thực hiện 2 bước:
- **Chế độ cửa sổ ứng dụng độc lập (Standalone Desktop Window):** Nâng cấp `START_STUDIO.bat` tự động khởi chạy server nền và mở **SplintFit Studio** dưới dạng cửa sổ ứng dụng Windows độc lập (`--app=http://127.0.0.1:8765 --window-size=1440,900`, không thanh địa chỉ, không tab trình duyệt) nhưng vẫn giữ trọn hiệu năng đồ họa 3D WebGL 60fps và hộp thoại chọn thư mục trực tiếp trên máy.
- **Dọn bỏ mã nguồn dư thừa:** Xóa hẳn tệp `engine/project_io.py` (tồn dư từ bản PyQt6 cũ không còn dùng) và xóa endpoint `api_browse_folder` (`tkinter`) đã được thay thế bởi File System Access API.

### 2. Trạng thái & Kết quả kiểm chứng
- **Kiểm thử tự động:** Đạt **2/2 bài kiểm tra (2,42 giây)** sau khi dọn mã nguồn — không phát sinh lỗi hồi quy (regression).
- **Cấu trúc dự án hiện tại gọn gàng theo 4 thư mục chức năng:** `engine/` (lõi hình học), `backend/` (máy chủ API), `frontend/` (giao diện 3D Wizard), `tests/` (kiểm thử tự động).

### 3. Hạn chế & Rủi ro đang mở
- Cần thực nghiệm mở trực tiếp `splint_form_piece_1_quad.obj` trong **Autodesk Fusion 360 (Create Form → Convert Quad Mesh to T-Splines)** để xác nhận toàn chuỗi quy trình tới sản phẩm CAD hoàn chỉnh.

### 4. Bước tiếp theo cần làm ngay
1. Mở `START_STUDIO.bat` bằng File Explorer để trải nghiệm chế độ cửa sổ ứng dụng máy tính độc lập.
2. Thực hiện kiểm chứng bước `Quad Mesh → T-Splines` trong Autodesk Fusion 360.

---

## Mốc 5 — 26/11/2026: Nâng cấp chọn thư mục trực tiếp trên trình duyệt (File System Access API)

### 1. Bối cảnh & Quyết định kỹ thuật
Khi chạy ứng dụng dưới dạng Web App cục bộ, việc mở hộp thoại chọn thư mục từ tiến trình nền Python (`tkinter`) dễ bị Windows chặn hiển thị đè lên trình duyệt. Để người dùng chọn nơi lưu tệp tự nhiên và ổn định 100% ngay trên Brave/Chrome/Edge, hệ thống đã chuyển sang kết hợp 2 cơ chế:
- **Chọn thư mục trực tiếp từ trình duyệt (`window.showDirectoryPicker` — File System Access API):** Khi bấm **📁 Chọn thư mục trên máy…**, chính trình duyệt sẽ bật cửa sổ Windows Explorer chuẩn ở lớp trên cùng và ghi thẳng 5 tệp `.obj`/`.stl` vào thư mục con `<Mã_ca>_<ngày_giờ>` ngay trong thư mục người dùng chọn.
- **3 nút chọn nhanh 1-click (`Desktop`, `Downloads`, `Documents`):** Hỗ trợ chọn nhanh đường dẫn chuẩn của Windows mà không cần mở hộp thoại, vẫn giữ song song nút **Tải gói .ZIP**.

### 2. Trạng thái & Kết quả kiểm chứng
- **Mã nguồn cập nhật:** `backend/server.py` (thêm API truyền từng tệp `/api/export/<id>/file/<path>` và `/api/user-folders`), `frontend/index.html`, `frontend/app.js`, `tests/test_studio_api.py`.
- **Kiểm thử tự động:** Đạt **2/2 bài kiểm tra (2,91 giây)** — xác nhận API truyền từng tệp, danh sách thư mục chuẩn Windows (`Desktop/Downloads/Documents`), gói 5 tệp All-Quad và chế độ xuất đầy đủ đều hoạt động chính xác.

### 3. Hạn chế & Rủi ro đang mở
- API `showDirectoryPicker` hoạt động chuẩn trên trình duyệt nhân Chromium (Brave, Chrome, Edge); trên Firefox/Safari hệ thống tự động hướng người dùng dùng 3 nút `Desktop / Downloads / Documents` hoặc `Tải gói .ZIP`.
- Vẫn cần thực nghiệm trực tiếp bước `Convert (Quad Mesh to T-Splines)` trong **Autodesk Fusion 360** trên máy người dùng.

### 4. Bước tiếp theo cần làm ngay
1. Người dùng tải lại trang `http://127.0.0.1:8765`, bấm **📁 Chọn thư mục trên máy…** để xuất thử 5 file mesh ra Desktop/Documents.
2. Nhập `splint_form_piece_1_quad.obj` vào **Autodesk Fusion 360 (Create Form)** theo hướng dẫn 7 bước.

---

## Mốc 4 — 26/11/2026: Tối ưu quy trình xuất lưới cho Fusion 360 & Chọn thư mục lưu linh hoạt

### 1. Bối cảnh & Quyết định kỹ thuật
Trong quá trình dùng thử, gói xuất cũ tạo ra hơn 12 tệp (gồm báo cáo, tệp xem 3D offline, STL gộp...) gây rối cho người dùng khi mục tiêu chính chỉ là đưa mô hình sang **Autodesk Fusion 360** để chỉnh dáng. Đồng thời, việc cố định thư mục lưu khiến người thao tác khó tìm tệp trên máy tính.

Nhóm phát triển đã chốt 2 cải tiến:
- **Gói xuất gọn chuyên biệt cho Fusion 360 Form (mặc định đúng 5 tệp sạch):**
  1. `splint_form_piece_1_quad.obj` và `splint_form_piece_2_quad.obj`: Lưới bề mặt trong thuần tứ giác (nền trơn chưa đục lỗ), tối ưu để kéo nắn mượt mà trong chế độ *Edit Form (T-Spline)*.
  2. `splint_form_perforated_piece_1_quad.obj` và `piece_2`: Lưới thuần tứ giác đã đục sẵn hệ lỗ thoáng tổ ong.
  3. `scan_reference_mm.stl`: Mô hình cánh tay gốc giữ nguyên hệ tọa độ `mm` để người dùng đối chiếu trực tiếp khe hở giữa nẹp và da trong Fusion 360.
  *(Tùy chọn xuất thêm STL in trực tiếp và báo cáo kỹ thuật vẫn được giữ dưới dạng ô tích phụ khi cần làm phụ lục báo cáo).*
- **Hộp thoại chọn nơi lưu tệp trực tiếp trên Windows:** Thêm nút **Chọn thư mục…** (mở cửa sổ chọn thư mục quen thuộc của Windows, tự nhớ lựa chọn cho lần sau), sửa cơ chế mở thư mục bằng `explorer.exe` và bổ sung nút **Sao chép đường dẫn**.

### 2. Trạng thái & Kết quả kiểm chứng
- **Mã nguồn cập nhật:** `backend/server.py`, `frontend/index.html`, `frontend/app.js`, `tests/test_studio_api.py`.
- **Kiểm thử tự động:** Đạt **2/2 bài kiểm tra (1,62 giây)** — xác nhận gói mặc định chỉ xuất đúng 5 tệp mesh, toàn bộ tệp `.obj` giữ cấu trúc thuần tứ giác 4 đỉnh/mặt, lưu đúng vào thư mục tùy chọn và không làm hỏng chế độ xuất đầy đủ.
- **Lưu trữ mã nguồn:** Đã đẩy toàn bộ dự án lên GitHub tại nhánh `studio-v2` (`Hoangcamng03/SplintFit-Prethesis`) nhằm bảo toàn nguyên vẹn phiên bản thử nghiệm cũ trên nhánh `main`.

### 3. Hạn chế & Rủi ro đang mở
- **Vị trí đường khoét đầu bàn tay (Hand Notch):** Hiện đang để góc mặc định `0°` (nằm giữa mặt lòng/mu theo chấm tím). Trên tay thật có ngón cái ở cạnh bên, người dùng cần xoay góc sang `±90°` hoặc chọn chế độ *Cắt thẳng* để tránh vết khoét lệch khỏi gốc ngón cái.
- **Kiểm chứng trên Fusion 360:** Chưa thực nghiệm trực tiếp thao tác chuyển đổi `Quad Mesh → T-Splines` trên phần mềm Autodesk Fusion 360 tại máy người dùng.

### 4. Bước tiếp theo cần làm ngay
1. Mở thử `splint_form_piece_1_quad.obj` và `scan_reference_mm.stl` trong **Autodesk Fusion 360 (Create Form)** để xác nhận độ tương thích thực tế.
2. Bổ sung nút chọn nhanh vị trí mở gốc ngón cái (`+90° / -90°`) ngay ngoài Bước 3 nếu người dùng muốn dùng vết khoét tự động.

---

## Mốc 3 — 25/11/2026: Cơ chế tự động khóa vùng an toàn (Safe-Zone) & Khắc phục lỗi trên file scan tay thật

### 1. Bối cảnh & Quyết định kỹ thuật
Khi thử nghiệm trên mô hình tay thật độ phân giải cao (`Hand and Forearm - Full.stl`, 158.894 mặt tam giác), có 3 vấn đề thực tế xuất hiện:
1. **Lỗi mất kết nối máy chủ (`Failed to fetch`):** Thư viện đồ họa 3D C++ (VTK/PyVista) không an toàn khi chạy đa luồng trên Windows, gây sập server khi xử lý tệp nặng. → **Giải pháp:** Chuyển server Flask sang chạy đơn luồng an toàn trên luồng chính (`threaded=False`).
2. **Lỗi chạm thành nẹp trên vùng cổ tay cong (`21 điểm scan nằm trong thành nẹp`):** Các mặt lưới quanh lỗ thoáng hơi dài gây hiện tượng võng dây cung (*chordal sag*) vào sát da. → **Giải pháp:** Thêm 1 vòng lưới chia trung gian quanh mỗi ô lỗ thoáng trong `cast_template.py`, giúp giảm độ võng 4 lần và làm bề mặt cong ôm cổ tay mượt hơn nhưng vẫn giữ 100% lưới tứ giác.
3. **Khó khăn khi người không chuyên tự chấm điểm trên 3D:** Việc tự chấm điểm dễ chạm nhầm vào ngón cái, đầu ngón tay hoặc mép cắt hở gây báo lỗi liên tục. → **Giải pháp:** Xây dựng thuật toán **Tự động khóa vùng an toàn (Safe-Zone)** quét 32 lát cắt dọc trục cánh tay ngay khi nạp tệp, tự loại trừ vùng ngón tay và mép hở; đồng thời chuyển Bước 2 sang **3 thanh trượt chỉnh trực tiếp trên 3D** (*Đầu khuỷu*, *Đầu bàn tay*, *Xoay hướng tách 2 mảnh 0°–180°*) bị giới hạn chặt trong vùng hợp lệ.

### 2. Trạng thái & Kết quả kiểm chứng
- **Thử nghiệm trên tệp tay thật `Hand and Forearm - Full.stl` (158.894 mặt):**
  - Tự động nhận diện đúng vùng cẳng tay–cổ tay hợp lệ dài **245,5 mm** (dừng gọn dưới gốc ngón cái).
  - Cả 3 cấu hình lâm sàng (**Đang sưng**, **Ổn định**, **Ôm sát**) và các kịch bản kéo thanh trượt thu ngắn/xoay góc (`245,5 mm / 0°` và `185,5 mm / 90°`) đều dựng thành công trong **~6,5 giây** (tăng tốc gấp đôi nhờ dùng chung 1 lần dựng mặt cắt cho cả 2 mảnh).
- **Kiểm thử tự động:** Đạt **2/2 bài kiểm tra (3,61 giây)**.

### 3. Hạn chế & Rủi ro đang mở
- Hệ thống v1 vẫn giới hạn trong vùng mặt cắt một vòng kín hướng tâm (phù hợp nẹp cổ tay–cẳng tay dưới khuỷu; chưa hỗ trợ nẹp khuỷu gập góc hoặc nhánh bọc riêng ngón cái *thumb spica*).

### 4. Bước tiếp theo cần làm ngay
- Rà soát độ gọn của gói xuất file cho Fusion 360 *(đã hoàn thành ở Mốc 4)*.

---

## Mốc 2 — 25/11/2026: Nâng cấp hình học nẹp thực tế & Đơn giản hóa giao diện cho Bác sĩ

### 1. Bối cảnh & Quyết định kỹ thuật
Từ góp ý thực tế đối với bản thử nghiệm trước đó (nẹp tạo ra còn thô như ống trụ đơn giản, giao diện nhiều thuật ngữ kỹ thuật gây rối cho bác sĩ), nhóm đã thực hiện 3 nâng cấp lớn:
- **Hình học nẹp chuẩn y tế hơn:**
  - Nâng cấp mẫu thử Sandbox sang mô hình **giải phẫu cẳng tay–cổ tay–bàn tay** (có thắt cổ tay, dẹt mặt lòng/mu, phình gò cái và mỏm trâm trụ nhẹ).
  - Thay thế lưới lỗ vuông thưa bằng **lưới lỗ thoáng tổ ong xếp so le** (bo tròn 16 cạnh giúp giảm tập trung ứng suất, tránh tạo đường yếu chạy dọc thân nẹp), giữ nguyên vành biên đặc và **3 dải ngang gia cường có khe luồn dây đai Velcro**.
  - Bổ sung **độ loe nhẹ ở 2 đầu mép (`1,4 mm`)** chống cấn cắt vào da, áp dụng đồng bộ lên cả file STL và lưới Quad cho Fusion 360.
- **Đơn giản hóa thông số sang ngôn ngữ lâm sàng:** Ở Bước 3, bác sĩ chỉ cần chọn **4 nhóm thẻ trực quan** (*Tình trạng tay*, *Độ cứng vỏ nẹp*, *Kiểu thoáng khí*, *Đường mở đầu bàn tay*). Toàn bộ thanh trượt số học CAD (`mm`, `độ`, khoảng cách lỗ, đối chiếu thước dây) được thu gọn vào mục *Tinh chỉnh nâng cao dành cho Kỹ thuật viên*.
- **Nhất quán hóa thao tác:** Mỗi bước chỉ có đúng **1 nút hành động chính duy nhất** cố định ở góc dưới phải.

### 2. Trạng thái & Kết quả kiểm chứng
- Kiểm thử tự động đạt **2/2 PASS (3,21 giây)**.
- Kiểm thử thực nghiệm 3 tổ hợp cấu hình lâm sàng đều đạt vỏ kín không va chạm bề mặt chi (*Ổn định + Tổ ong*: 36 lỗ thoáng, 12 khe đai, 1.008 ô Quad; *Đang sưng + Cứng*: 24 lỗ thoáng; *Ôm sát + Vỏ kín*: đã hiệu chỉnh khoảng hở tối thiểu từ `1,0 mm` lên `1,3 mm` để tránh cấn vùng gò cái).

### 3. Hạn chế & Rủi ro đang mở
- Chưa thử nghiệm trên file scan tay thật độ phân giải cao *(đã thực hiện và khắc phục lỗi ở Mốc 3)*.

---

## Mốc 1 — 25/11/2026: Khởi tạo kiến trúc SplintFit Studio (Web App cục bộ)

### 1. Bối cảnh & Quyết định kỹ thuật
- **Chuyển đổi nền tảng giao diện:** Thay vì dùng ứng dụng desktop PyQt6 cũ (nặng, dễ khựng khi xoay 3D và bố cục khô cứng), dự án được xây dựng mới theo mô hình **Web App chạy cục bộ (Local Web App)**: phía sau dùng **Python 3.12 (Flask)** tái sử dụng lõi toán học hình học (`engine/`), phía trước dùng giao diện web hiện đại kết hợp **Three.js (WebGL)** cho phép xoay/phóng 3D mượt mà trên trình duyệt Chrome/Edge/Brave.
- **Quy trình 5 bước dẫn dắt (Wizard):** `1. Nạp Scan → 2. Chọn Vùng → 3. Thiết Kế → 4. Kiểm Tra 3D & Lưới Form → 5. Xuất Fusion 360`, bổ sung thanh kéo **Tách 2 mảnh (Exploded View)** và bật/tắt **Lưới Quad** trực tiếp trên khung 3D.
- **Chốt phạm vi v1:** Tập trung hoàn thiện trọn vẹn luồng thiết kế **nẹp cổ tay–cẳng tay 2 mảnh (dưới khuỷu)** trước khi mở rộng sang các vùng giải phẫu phức tạp hơn ở giai đoạn Thesis.

### 2. Trạng thái & Kết quả kiểm chứng
- Hoàn thiện cấu trúc dự án tách bạch tại `SplintFit-Studio/` (`engine/`, `backend/`, `frontend/`, `tests/`, `START_STUDIO.bat`).
- Bộ kiểm thử tự động đầu tiên (`tests/test_studio_api.py`) đạt **2/2 PASS (3,19 giây)**.

---

## Phụ lục: Giải thích nhanh thuật ngữ cho người không chuyên

| Thuật ngữ | Giải thích dễ hiểu |
| :--- | :--- |
| **No Hole Filling (Không tự vá lỗ)** | Phần mềm không tự động bịa thêm bề mặt vào chỗ file scan bị thiếu dữ liệu, nhằm tránh làm nẹp bị phồng hoặc ép sai vào da bệnh nhân. |
| **All-Quad Mesh (Lưới thuần tứ giác)** | Bề mặt 3D được ghép hoàn toàn từ các ô 4 cạnh đều nhau (thay vì tam giác lộn xộn). Đây là điều kiện bắt buộc để **Autodesk Fusion 360** chuyển sang chế độ **Form (T-Spline)** và kéo nắn dáng mượt mà. |
| **Safe-Zone (Vùng an toàn)** | Đoạn cẳng tay–cổ tay mà phần mềm đã tự kiểm tra là kín, tròn đều và không dính ngón tay; các thanh trượt được khóa trong vùng này để người dùng không thể chỉnh nhầm gây lỗi. |
| **Loe mép (Rim Flare)** | Hai đầu nẹp được mở loe nhẹ ra ngoài khoảng `1,4 mm` giúp viền nhựa không đâm hoặc cấn vào da khi cử động tay. |
| **Kiểm tra vỏ kín (Watertight)** | Đảm bảo mô hình nẹp 3D tạo thành một khối đặc kín hoàn toàn, không bị thủng mặt hay lỗi cạnh để máy in 3D có thể cắt lớp và in được. |
