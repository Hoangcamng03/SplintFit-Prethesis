# NHẬT KÝ PHÁT TRIỂN DỰ ÁN (CAPSTONE LAB NOTEBOOK)
## Đề tài: SplintFit Studio — Hệ thống bán tự động thiết kế nẹp cổ tay–cẳng tay 3D cá thể hóa kết hợp Autodesk Fusion 360 (Form / T-Spline)

- **Lĩnh vực:** Kỹ thuật Y sinh (Biomedical Engineering) — Pre-thesis / Hướng tới Capstone Thesis
- **Mục tiêu tổng quát:** Xây dựng phần mềm trực quan, dễ thao tác cho cả **bác sĩ và kỹ thuật viên không chuyên CAD 3D**, giúp chuyển đổi trực tiếp mô hình quét 3D cánh tay (từ KIRI Engine) thành mẫu nẹp 2 mảnh cá thể hóa an toàn và xuất lưới tứ giác chuẩn (**All-Quad Mesh**) để hiệu chỉnh thủ công trong **Autodesk Fusion 360 (chế độ Form / T-Spline)** trước khi in 3D.
- **Chuỗi quy trình kỹ thuật (End-to-End Pipeline):**
  `Quét 3D tay (KIRI Engine) → SplintFit Studio (Xử lý & Tạo hình nẹp) → Autodesk Fusion 360 (Chỉnh Form & Bo mép) → In 3D kiểm thử`
- **Nguyên tắc an toàn cốt lõi:** **Không tự động vá lỗ quét (No Hole Filling)** trên vùng tiếp xúc da để tránh tạo ra bề mặt giả có thể gây cấn hoặc loét tỳ đè.

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
