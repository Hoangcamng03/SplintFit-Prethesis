# HƯỚNG DẪN SỬ DỤNG & GIẢI THÍCH THÔNG SỐ — SPLINTFIT STUDIO (v3.2)

Tài liệu này hướng dẫn chi tiết cách vận hành **SplintFit Studio Desktop** từ lúc nạp file quét 3D cánh tay cho tới khi chỉnh sửa ở chế độ **Form (T-Spline)** trên **Autodesk Fusion 360** và xuất file in 3D, kèm bảng giải thích dễ hiểu cho toàn bộ thông số trên giao diện (dành cho **Bác sĩ, Kỹ thuật viên và Sinh viên Kỹ thuật Y sinh**).

---

## 1. Tổng quan & Phạm vi hỗ trợ
- **Ứng dụng:** Phần mềm máy tính Windows độc lập (`PyQt6 + PyVistaQt`), không cần trình duyệt.
- **Phạm vi hình học (v3.2):** Thiết kế **nẹp cổ tay – cẳng tay (dưới khuỷu)** dạng **2 mảnh tháo lắp** hoặc **1 mảnh máng hở** từ file quét 3D (`.stl`, `.obj`, `.ply`) xuất từ KIRI Engine hoặc máy quét quang học (Artec, Revopoint...).
- **Nguyên tắc an toàn cốt lõi:** **Không tự động vá lỗ quét (*No Hole Filling*)** trên vùng tiếp xúc da để tránh tạo bề mặt giả gây cấn hoặc loét tỳ đè.
- **Cách mở phần mềm:** Mở thư mục dự án (`D:\SplintFit3D\App`) bằng **File Explorer** → nhấp đúp **`START_STUDIO.bat`**.

---

## 2. Hướng dẫn thao tác chi tiết 5 bước trên SplintFit Studio

### Bước 1 — Nạp file quét 3D cánh tay
1. Ở góc trên bên phải, nhập **Mã ca** (ví dụ `A` hoặc `CASE-001`) và chọn **Tay trái / Tay phải**. Tên các file xuất ra ở Bước 5 sẽ tự đặt theo Mã ca này.
2. Chọn **Đơn vị file** khớp với file quét gốc (mặc định **`Milimét (mm)`**).
   - *Mẹo kiểm tra nhanh:* Sau khi nạp, nhìn ô **Chiều dài mẫu**. Cả cánh tay + bàn tay thật dài khoảng **280–450 mm** (riêng cẳng tay khoảng **160–260 mm**). Nếu thấy số quá nhỏ (ví dụ `0.35 mm` hoặc `35 mm`), hãy đổi đơn vị sang **`Mét (m)`** hoặc **`Xentimét (cm)`** rồi nạp lại.
3. Giữ tích ô **`Tự động xác định 3 mốc & dựng sẵn nẹp 2 mảnh ngay khi nạp file`**.
4. Bấm **`📂 Chọn file .STL / .OBJ / .PLY trên máy…`** để mở file tay thật (hoặc bấm **`Mẫu cẳng tay – bàn tay`** để thử nhanh).
5. Nếu file có nhiều mảnh rác lơ lửng xung quanh, chọn **`Khối #1`** (khối lớn nhất) ở mục *Chọn phần cánh tay chính*.
6. Chờ ~3–6 giây: phần mềm tự gắn 3 nhãn 3D (**`1. Elbow`**, **`2. Wrist`**, **`3. Splint Side`**), dựng luôn nẹp 2 mảnh và tự chuyển sang **Bước 2**.

### Bước 2 — Chỉnh vùng đặt nẹp (Tự khóa vùng an toàn — Safe-Zone)
Hệ thống đã tự dò 32 lát cắt dọc cánh tay để khóa chặt **Vùng an toàn** (tự né mép cắt hở ở đầu khuỷu và tự dừng trước khi tách ngón cái/4 ngón tay). Bạn chỉ cần dùng **3 thanh trượt trực tiếp trên 3D**:
1. **`1. Đầu phía khuỷu tay (Vòng xanh)`:** Kéo sang phải để rút ngắn đầu khuỷu. Không bao giờ kéo lố ra mép hở.
2. **`2. Đầu phía bàn tay (Vòng cam)`:** Kéo để chỉnh vị trí dừng gần cổ tay/dưới gốc ngón cái. Không bao giờ kéo lố lên ngón tay.
3. **`3. Xoay hướng tách 2 mảnh (Chấm tím, 0°–180°)`:** Xoay chấm tím **`3. Splint Side`** về chính giữa mặt mu hoặc mặt lòng cẳng tay để **khe tách 2 mảnh nằm gọn ở 2 bên cạnh tay** (bờ trụ và bờ quay).
4. Nếu có kéo chỉnh, bấm **`Cập nhật lại nẹp 3D theo vị trí vừa chỉnh`**, rồi bấm **`Tiếp tục thiết kế →`**.

### Bước 3 — Chọn cấu hình nẹp lâm sàng
- Bác sĩ chỉ cần bấm chọn **5 nhóm thẻ trực quan** bằng tiếng Việt (chi tiết ở Mục 3 bên dưới).
- Kỹ thuật viên muốn chỉnh sâu theo từng milimét có thể bấm mở mục **`⚙️ Tinh chỉnh nâng cao (Dành cho Kỹ thuật viên)`**.
- Bấm **`Tạo mô hình nẹp 3D`** → phần mềm dựng nẹp và tự chuyển sang **Bước 4**.

### Bước 4 — Kiểm tra mô hình 3D & Lưới Fusion Form
Dùng thanh công cụ phía dưới khung 3D:
- **`Chi quét` + thanh `Mờ chi`:** Làm mờ cánh tay gốc để soi khe hở giữa da và mặt trong nẹp.
- **`Biên hở`:** Hiển thị các cạnh hở màu đỏ của file scan gốc.
- **`Vỏ nẹp 3D`:** Hiển thị 2 mảnh nẹp (xanh lục & xanh dương) với lưới thoáng tổ ong và loe mép.
- **`Lưới Quad (Fusion Form)`:** Bật lưới khung dây thuần tứ giác sẽ đưa sang Fusion 360.
- **`Độ thoáng mặt trong`:** Xem bản đồ màu phân bố khoảng hở giữa mặt trong nẹp và bề mặt da.
- **`Tách 2 mảnh`:** Kéo thanh trượt để tách đôi 2 mảnh nẹp, quan sát kỹ mặt trong và các lỗ thoáng.
- Xem bảng **Kiểm tra an toàn hình học** bên phải, rồi bấm **`Sang bước xuất Fusion 360 →`**.

### Bước 5 — Chọn thư mục lưu & Xuất file cho Fusion 360 Form
1. Bấm **`📁 Chọn thư mục…`** (hoặc bấm nhanh **`Desktop` / `Downloads` / `Documents`**) để chọn nơi lưu trên máy tính (app tự nhớ thư mục cho lần sau).
2. Bấm **`Xuất lưới cho Fusion 360 Form`**. Với Mã ca là **`A`**, app tạo thư mục con `A_<ngày_giờ>` chứa gọn **đúng 5 file mesh**:
   - **`A-1.obj`** & **`A-2.obj`** *(Khuyên dùng cho Fusion Form)*: Lưới mặt trong thuần tứ giác (All-Quad), nền trơn chưa đục lỗ, đã cộng sẵn khoảng hở + lớp đệm + loe mép.
   - **`A-1_holes.obj`** & **`A-2_holes.obj`**: Bản All-Quad đã đục sẵn lỗ thoáng tổ ong & khe dây đai.
   - **`A_scan.stl`**: Cánh tay gốc giữ đúng hệ tọa độ `mm` để đối chiếu khe hở trong Fusion 360.
   - *(Nếu cần thêm STL in trực tiếp, báo cáo JSON và file xem 3D HTML cho phụ lục báo cáo, tích ô tùy chọn phía trên nút xuất).*
3. Bấm **`📂 Mở thư mục vừa xuất trong Windows Explorer`** để truy cập ngay các file vừa tạo.

---

## 3. Giải thích chi tiết toàn bộ thông số trên app

### 3.1. Các nhóm thẻ cấu hình lâm sàng (Dành cho Bác sĩ & Kỹ thuật viên)

| Nhóm thẻ | Lựa chọn | Giá trị kỹ thuật tự áp | Ý nghĩa & Khi nào nên chọn |
| :--- | :--- | :--- | :--- |
| **0. Cấu trúc nẹp** | **Nẹp 2 mảnh tháo lắp** *(mặc định)* | `bivalve`, khe `4,0 mm`, 3 dải đai | Dễ đeo/tháo, dễ chỉnh độ siết bằng dây Velcro khi tay thay đổi độ sưng. |
| | **Nẹp 1 mảnh máng hở** | `single`, góc ôm `180°` | Dạng máng nâng đỡ một mặt (mu hoặc lòng), tháo lắp nhanh. |
| **1. Tình trạng tay** | **Đang sưng** | Hở da `2,5 mm` + Lót `1,0 mm` | Giai đoạn cấp / mới bó, dự phòng sưng nề và có dán mút lót dày. |
| | **Ổn định** *(mặc định)* | Hở da `1,5 mm` + Lót `0,5 mm` | Giai đoạn ổn định, ôm vừa vặn có lót vải/mút mỏng. |
| | **Ôm sát** | Hở da `1,3 mm` + Lót `0,0 mm` | Đeo trực tiếp không dán mút lót (vẫn giữ khe tối thiểu tránh cấn da). |
| **2. Độ cứng vỏ nẹp** | **Nhẹ** | Thành dày `2,8 mm` | Nẹp nhẹ, ít cồng kềnh cho hỗ trợ nhẹ hoặc tay nhỏ. |
| | **Tiêu chuẩn** *(mặc định)* | Thành dày `3,2 mm` | Cân bằng giữa độ cứng cố định và trọng lượng khi in PLA/PETG. |
| | **Cứng chắc** | Thành dày `4,0 mm` | Tăng độ cứng chống uốn cho cẳng tay lớn hoặc cần bất động chắc hơn. |
| **3. Lưới thoáng khí** | **Tổ ong thoáng** *(mặc định)* | Bước lỗ `20 mm`, tỷ lệ `0,58` | Lưới lỗ xếp so le thoáng khí cao, giảm trọng lượng và giảm hầm bí da. |
| | **Thoáng vừa** | Bước lỗ `25 mm`, tỷ lệ `0,48` | Vách nhựa giữa các lỗ dày hơn, tăng độ bền kết cấu. |
| | **Vỏ kín** | Tắt đục lỗ (`ventilation = False`) | Bề mặt đặc hoàn toàn (dùng khi muốn tự thiết kế hoa văn lỗ trong Fusion 360). |
| **4. Đường mở bàn tay** | **Mở rộng** | Khoét chữ U sâu `22 mm` | Mở rộng không gian cử động vùng cổ tay / gốc ngón cái. |
| | **Vừa phải** | Khoét chữ U sâu `14 mm` | Khoét nhẹ đầu bàn tay. |
| | **Cắt thẳng** *(khuyên cho Form)* | Sâu `0 mm` | Đầu nẹp cắt phẳng đều — **đẹp và dễ kéo chỉnh nhất khi đưa vào Fusion 360 Form**. |

### 3.2. Các thông số trong mục "⚙️ Tinh chỉnh nâng cao (Kỹ thuật viên)"

| Thông số | Khoảng giá trị | Giải thích dễ hiểu & Tác động |
| :--- | :--- | :--- |
| **Khoảng hở thoáng da (`clearance_mm`)** | `0,5 – 6,0 mm` | Khe hở cơ bản giữa bề mặt da quét và mặt trong nẹp. Tăng lên giúp thoáng và giảm nguy cơ cấn khi tay sưng; quá lớn sẽ làm nẹp bị lỏng. |
| **Độ dày lớp lót mút (`padding_mm`)** | `0,0 – 5,0 mm` | Khoảng cộng thêm đúng bằng độ dày miếng mút/vải lót bạn định dán bên trong nẹp. Tổng khoảng đẩy mặt trong = `Khoảng hở + Lớp lót`. |
| **Độ dày thành nhựa (`thickness_mm`)** | `2,0 – 6,0 mm` | Độ dày vỏ nẹp in 3D (đẩy ra phía ngoài). Giá trị này cũng là số bạn nhập vào lệnh `Thicken` trong Fusion 360. |
| **Độ loe nhẹ mép 2 đầu (`rim_flare_mm`)** | `0,0 – 3,5 mm` | Mở loe nhẹ ~14 mm ở hai đầu khuỷu và bàn tay ra phía ngoài (mặc định `1,4 mm`) để mép nhựa không đâm/cắt vào da khi cử động. |
| **Khe hở tách 2 mảnh (`seam_gap_mm`)** | `2,0 – 12,0 mm` | Khoảng trống giữa mảnh 1 và mảnh 2 dọc 2 bên cạnh tay, giúp 2 mảnh không đụng nhau khi siết dây đai Velcro. |
| **Khoảng cách tâm lỗ (`hole_pitch_mm`)** | `16 – 38 mm` | Bước lưới giữa các ô lỗ thoáng. Số nhỏ hơn → nhiều lỗ nhỏ hơn; số lớn hơn → ít lỗ nhưng lỗ lớn hơn. |
| **Độ mở lỗ trên ô (`hole_ratio`)** | `0,25 – 0,65` | Tỷ lệ kích thước lỗ so với ô lưới (không phải % tổng diện tích). Bị giới hạn tối đa `0,65` để vách nhựa giữa các lỗ không quá mỏng. |
| **Độ sâu đường mở bàn tay (`hand_notch_depth_mm`)** | `0 – 45 mm` | Chiều sâu đường khuyết chữ U ở đầu phía bàn tay (`0` = cắt thẳng). |
| **Hướng xoay góc mở (`hand_notch_angle_deg`)** | `-180° đến +180°` | Vị trí góc quanh chu vi cổ tay nơi cắt rãnh chữ U, **lấy chấm tím `3. Splint Side` làm mốc `0°`**: `0°` = giữa mảnh xanh lục; `+90°` hoặc `-90°` = 2 cạnh bên (phía ngón cái / ngón út); `180°` = giữa mảnh xanh dương. |

> **Quy tắc tạo lỗ thoáng (không ngẫu nhiên):** Phần mềm giữ **đặc hoàn toàn** 2 hàng mép đầu/cuối và 2 cột biên dọc khe tách để tạo khung chịu lực; giữ đặc 3 dải ngang ở vị trí `20%`, `50%`, `80%` chiều dài (chỉ mở khe hẹp ở 2 biên để luồn dây đai Velcro); các hàng lỗ giữa được **xếp so le (hàng gạch/tổ ong)** và **bo tròn 16 cạnh** nhằm giảm tập trung ứng suất và tránh tạo đường gãy thẳng dọc thân nẹp.

---

## 4. Hướng dẫn 6 bước đưa vào Autodesk Fusion 360 (Chế độ Form / T-Spline)

*(Đã kiểm chứng thực tế trên Autodesk Fusion Education License 2026 với file xuất từ Mã ca `A`)*:

1. **Kiểm tra đơn vị:** Ở màn hình thường (**tab `SOLID`**), nhìn cột **Browser** bên trái → `Document Settings → Units` đảm bảo đang là **`mm`**.
2. **Chèn mảnh nẹp 1 (`A-1.obj`):** Bấm **`INSERT` → `Insert Mesh`** → **`Select from my computer…`** → chọn **`A-1.obj`**.
   - Ở bảng `INSERT MESH` bên phải: **`Unit Type = Millimeter`**, **KHÔNG bấm** `Center` hay `Move to Ground` → bấm **`OK`**.
3. **Chèn cánh tay mẫu đối chiếu (`A_scan.stl`, tùy chọn):** Bấm **`INSERT` → `Insert Mesh`** → chọn **`A_scan.stl`** (`Millimeter`, giữ nguyên tọa độ gốc → **`OK`**).
   - Ở cột **Browser → `Bodies`**, chuột phải vào `A_scan` → **`Opacity Control → 40%`** (hoặc bấm biểu tượng **con mắt** tạm ẩn đi cho dễ chọn mảnh nẹp).
4. **Chuyển `A-1.obj` sang Form (T-Spline):**
   - Ở tab **`SOLID`**, bấm **`Create Form`** (biểu tượng **khối hộp màu tím**).
   - Trên tab **`FORM`**, bấm **`UTILITIES` → `Convert`**.
   - Chọn **`Convert Type: Quad Mesh to T-Splines`** → nhấp chuột trái vào mảnh lưới **`A-1`** → bấm **`OK`**.
   - *Kết quả đúng:* Lưới `A-1` biến thành **bề mặt cong mịn** sẵn sàng kéo nắn.
5. **Kéo nắn dáng nẹp:** Bấm **`MODIFY` → `Edit Form`** (phím tắt **`Alt + 1`**), chọn điểm/cạnh/mặt rồi kéo mũi tên để chỉnh dáng theo cánh tay mẫu → bấm **`OK`** → bấm **`FINISH FORM`** (dấu tích xanh lá).
6. **Tạo độ dày ra ngoài, bo mép & xuất in 3D:**
   - Chuyển sang tab **`SURFACE`** → **`CREATE` → `Thicken`** → chọn bề mặt nẹp → nhập độ dày (ví dụ **`3.2 mm`**). **Quan sát kỹ hướng dày đẩy RA NGOÀI cánh tay** (nếu bị đẩy ngược vào trong thì đổi dấu thành **`-3.2 mm`**) → **`OK`** *(không cộng lại khoảng hở vì `A-1.obj` đã có sẵn)*.
   - Chuyển sang tab **`SOLID`** → **`MODIFY` → `Fillet`** → chọn các cạnh viền bo **`1 mm`** → **`OK`**.
   - Lưu file dự án `.f3d` (`Ctrl + S`), và chuột phải vào Solid Body trong `Bodies` → **`Save As Mesh`** (`STL Binary`, `Millimeter`) khi cần in 3D. *(Lặp lại bước 2–6 cho mảnh 2: `A-2.obj`).*

---

## 5. Xử lý nhanh các tình huống thường gặp

| Tình huống | Nguyên nhân | Cách xử lý |
| :--- | :--- | :--- |
| **Chiều dài mẫu hiện quá nhỏ (`0,3 mm`) hoặc quá lớn (`3000 mm`)** | File scan gốc xuất theo đơn vị `m` hoặc `cm`. | Chọn lại **Đơn vị file** ở Bước 1 (`cm` hoặc `m`) rồi nạp lại. |
| **Đường khoét chữ U ở đầu bàn tay bị lệch khỏi ngón cái** | Góc mở mặc định `0°` nằm giữa mặt lòng/mu, còn ngón cái nằm ở cạnh bên (`±90°`). | Mở *Tinh chỉnh nâng cao* đổi *Hướng xoay góc mở* sang `90°` hoặc `-90°`, hoặc chọn thẻ **Cắt thẳng** để tự chỉnh trong Fusion 360 Form. |
| **Không thấy lệnh `Insert Mesh` trong Fusion 360** | Bạn đang đứng bên trong tab **`FORM`**. | Bấm **`FINISH FORM`** thoát ra tab **`SOLID`** trước rồi mới bấm `INSERT → Insert Mesh`. |
| **Lệnh `Thicken` trong Fusion bị đâm ngược vào cánh tay** | Chiều pháp tuyến đẩy vào trong. | Đổi dấu độ dày (ví dụ từ `3.2 mm` thành `-3.2 mm`). |

