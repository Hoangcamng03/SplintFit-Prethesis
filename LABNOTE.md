# LABNOTE — SplintFit Studio (Pre-thesis / Thesis)

## Mốc 4 — 2026-11-26: Gói xuất gọn 5 mesh Fusion 360 Form & Chọn thư mục lưu tùy ý

### 1. Quyết định đã chốt & việc đã xong
- **Gói xuất gọn cho Fusion 360 Form (`backend/server.py`, `frontend/`):**
  - Mặc định ở Bước 5 chỉ xuất **đúng 5 file mesh sạch**: `splint_form_piece_1_quad.obj`, `splint_form_piece_2_quad.obj`, `splint_form_perforated_piece_1_quad.obj`, `splint_form_perforated_piece_2_quad.obj`, và `scan_reference_mm.stl` (giữ tùy chọn tích phụ nếu cần xuất kèm STL in 3D & báo cáo JSON).
- **Chọn nơi lưu file tùy ý & khắc phục nút mở thư mục:**
  - Thêm endpoint `POST /api/browse-folder` mở hộp thoại chọn thư mục Windows (`tkinter.filedialog`), lưu nhớ đường dẫn vào `localStorage`, và cho phép truyền `output_dir` vào `POST /api/export`.
  - Đổi nút mở thư mục sang `explorer.exe` kèm thêm nút **Sao chép đường dẫn**.

### 2. Trạng thái hiện tại
- `tests/test_studio_api.py`: **2/2 PASS (1,62s)** — xác minh gói mặc định đúng 5 file mesh, All-Quad 4 đỉnh/mặt, lưu đúng vào `output_dir` tùy chọn, và giữ nguyên chế độ xuất đầy đủ.
- Server đang chạy tại `http://127.0.0.1:8765`.

### 3. Nghi vấn / Rủi ro đang mở
- Đường khoét chữ U (`hand_notch_angle_deg`) hiện mặc định `0°` (trùng chấm tím ở mặt mu/lòng) nên trên tay thật có thể lệch `90°` so với ngón cái nếu chưa đổi sang `±90°` hoặc chọn *Cắt thẳng*.
- Chưa đẩy mã nguồn `SplintFit-Studio` lên GitHub để lấy link source.
- Chưa kiểm chứng trực tiếp bước `Quad Mesh → T-Splines` trong Autodesk Fusion 360 trên máy người dùng.

### 4. Bước tiếp theo cần làm ngay
1. Khởi tạo Git và đẩy dự án `SplintFit-Studio` lên GitHub (có `.gitignore` loại trừ `exports/` và file tạm) để gửi link repo cho người dùng.
2. Thêm nút chọn nhanh phía ngón cái (`+90° / -90°`) ngay ngoài Bước 3 nếu người dùng cần.
3. Kiểm chứng mở `splint_form_piece_1_quad.obj` trong **Autodesk Fusion 360 Form**.

---

## Mốc 3 — 2026-11-25: Khóa vùng an toàn tự động (Safe-Zone) + 3 thanh trượt 3D chống lỗi

### 1. Quyết định đã chốt & việc đã xong
- **Khắc phục lỗi thực tế trên file scan tay thật (`Hand and Forearm - Full.stl`, 158.894 mặt):**
  - Chuyển Flask sang đơn luồng (`threaded=False`) chống sập VTK trên Windows (`Failed to fetch`).
  - Thêm vòng lưới trung gian (midpoint ring) trong `cast_template.py` giảm 4× độ võng dây cung (chordal sag) trên cổ tay cong, vẫn giữ 100% All-Quad cho Fusion 360 Form.
- **Tự động khóa vùng an toàn & 3 thanh trượt Bước 2 (`geometry.py`, `server.py`, `frontend/`):**
  - `suggested_points()` quét 32 lát cắt dọc trục, trả về `safe_frame` (trục trung tâm cẳng tay + khoảng an toàn `[safe_min_mm, safe_max_mm]` + bán kính ước lượng).
  - Bước 2 đổi sang **3 thanh trượt 60fps** bị giới hạn trong vùng an toàn (*Đầu khuỷu*, *Đầu bàn tay*, *Xoay hướng tách 2 mảnh 0°–180°*), triệt tiêu lỗi đặt điểm quá tay vào ngón cái hoặc mép hở; giữ chấm thủ công 3D trong mục Kỹ thuật viên.

### 2. Trạng thái hiện tại
- Unit tests (`tests/test_studio_api.py`): **2/2 PASS (3,61s)**.
- Đã xác minh trên `Hand and Forearm - Full.stl`: tự động nhận diện vùng an toàn `245,5 mm` (`radius_est = 31,27 mm`).

### 3. Nghi vấn / Rủi ro đang mở
- Cần test mở file xuất `splint_form_piece_1_quad.obj` trực tiếp trong **Autodesk Fusion 360 (Create Form → Quad Mesh to T-Splines)**.

### 4. Bước tiếp theo cần làm ngay
1. Khởi động lại `START_STUDIO.bat` để trải nghiệm 3 thanh trượt vùng an toàn ở Bước 2 trên `Hand and Forearm - Full.stl`.
2. Xuất gói ở Bước 5 và test chỉnh sửa Form (T-Spline) trong Fusion 360.

---

## Mốc 2 — 2026-11-25: Nâng cấp v2.0 (Lưới tổ ong so le, Loe mép, Mẫu giải phẫu & Preset lâm sàng)

### 1. Quyết định đã chốt & việc đã xong
- **Hình học nẹp (`engine/cast_template.py`):**
  - Nâng cấp `hand_demo_mesh()` lên mô hình giải phẫu cẳng tay – cổ tay – bàn tay (có độ dẹt lòng/mu, thắt cổ tay, gò cái *thenar* và mỏm trâm trụ nhẹ).
  - Thay lưới lỗ vuông thưa bằng **lưới thoáng tổ ong so le (brick-staggered conforming all-quad lattice)** dùng biên đồng nhất 5 điểm để bảo đảm 100% vỏ kín (`edge_watertight=True`, không lỗi manifold).
  - Bổ sung **loe nhẹ mép 2 đầu (`rim_flare_mm = 1.4 mm`)** chống cấn da, áp dụng đồng bộ lên cả STL lẫn Quad OBJ cho Fusion 360 Form.
- **Giao diện cho Bác sĩ & Kỹ thuật viên (`frontend/`):**
  - Bước 3 chuyển sang **4 nhóm thẻ Preset lâm sàng** bằng tiếng Việt trực quan (*Tình trạng tay*, *Độ cứng*, *Mức thoáng khí*, *Đường mở bàn tay*); gom toàn bộ thông số số học CAD vào mục mở rộng *Tinh chỉnh nâng cao*.
  - Nhất quán hóa thanh chân trang thành **1 nút hành động chính duy nhất mỗi bước**.

### 2. Trạng thái hiện tại
- `tests/test_studio_api.py`: **2/2 PASS (3,21s)**, xác minh vỏ kín 2 mảnh và file `*_quad.obj` thuần tứ giác 4 đỉnh/mặt.
- Đã kiểm thử thêm các tổ hợp Preset lâm sàng (Ổn định + Tổ ong, Đang sưng + Cứng, Ôm sát + Vỏ kín).

### 3. Nghi vấn / Rủi ro đang mở
- Cần kiểm chứng trực quan trên trình duyệt Chrome/Edge bằng `START_STUDIO.bat` và test mở `splint_form_piece_1_quad.obj` trong **Autodesk Fusion 360 (Create Form)**.
- Cần kiểm thử với 1 file scan tay thật từ **KIRI Engine**.

### 4. Bước tiếp theo cần làm ngay
1. Người dùng chạy `START_STUDIO.bat` để trải nghiệm bản v2.0.
2. Xuất gói mẫu thử ở Bước 5 và kiểm tra chuyển đổi `Quad Mesh → T-Spline` trong Fusion 360.

---

## Mốc 1 — 2026-11-25: Khởi tạo SplintFit Studio (Web App Local + Fusion 360 Form)

### 1. Quyết định đã chốt & việc đã xong (Decision Log)
- **Nền tảng:** Chuyển từ giao diện PyQt6 cũ sang **Local Web App** (`Flask` backend Python 3.12 + giao diện web hiện đại + `Three.js` 3D Studio chạy trên Chrome/Edge).
- **Phạm vi v1:** Tập trung làm tốt **nẹp cổ tay–cẳng tay 2 mảnh (dưới khuỷu)** với lỗ thoáng khí oval, khe luồn dây đai, đường khoét bàn tay, không dùng Hole Filling tự động trên vùng tiếp xúc da.
- **Tích hợp Autodesk Fusion 360 Form (T-Spline):**
  - Xuất lưới **All-Quad OBJ** nền trơn (`splint_form_piece_1_quad.obj`, `piece_2`) và bản có lỗ (`splint_form_perforated_piece_*_quad.obj`).
  - Xuất kèm `scan_reference_mm.stl` cùng hệ tọa độ `mm`, `fusion_user_parameters.json`, script `fusion/SplintFitImport`, và `shell_piece_*_prototype.stl`.
  - Tích hợp sẵn chế độ xem **Lưới Quad (Fusion Form)**, **Tách 2 mảnh (Explode)** và **Checklist 6 bước đưa vào Fusion 360 Form** ngay trong giao diện.
- **Tái sử dụng lõi hình học:** Đóng gói sạch `engine/` từ prototype v4 (`geometry.py`, `cast_template.py`, `measurements.py`, `project_io.py`) tách biệt hoàn toàn khỏi giao diện.

### 2. Trạng thái hiện tại
- Đã tạo cấu trúc dự án mới tại `C:\Users\USER\.gemini\antigravity\scratch\SplintFit-Studio`.
- Đã hoàn thiện `backend/server.py`, `frontend/{index.html,styles.css,app.js}`, `START_STUDIO.bat`, và bộ kiểm thử `tests/test_studio_api.py`.
- **Kết quả kiểm thử tự động:** `2/2 tests PASS` trong `3.19s` (nạp scan → dựng nẹp 2 mảnh có lỗ thoáng + khe dây đai → xuất đủ gói file Fusion 360 Form + STL + ZIP; xác minh toàn bộ file `*_quad.obj` thuần tứ giác 4 đỉnh/mặt).

### 3. Nghi vấn / Rủi ro đang mở
- **Chưa test thực tế trong Autodesk Fusion 360 trên máy người dùng:** Cần xác nhận quá trình `Insert Mesh (mm) → Convert (Quad Mesh to T-Splines) → Edit Form → Finish Form → Surface Thicken` chạy mượt với file `splint_form_piece_1_quad.obj`.
- **Chưa test với file scan tay thật từ KIRI Engine:** Mới kiểm chứng trên mô hình cẳng tay–bàn tay giả lập (`hand_demo_mesh`).
- **Chưa kiểm chứng lâm sàng & in 3D thực tế:** Chưa bo mép tự động (cần bo trong Fusion 360) và chưa đánh giá cơ tính / vừa vặn vật lý.

### 4. Bước tiếp theo cần làm ngay
1. Chạy `START_STUDIO.bat` để người dùng trải nghiệm giao diện mới trên Chrome/Edge và phản hồi những điểm muốn tinh chỉnh thêm.
2. Xuất gói mẫu thử từ Bước 5 và mở thử `splint_form_piece_1_quad.obj` trong **Autodesk Fusion 360 (Create Form)**.
3. Thử nạp 1 file scan tay thật từ **KIRI Engine** + đối chiếu thước dây để tinh chỉnh quy trình.
