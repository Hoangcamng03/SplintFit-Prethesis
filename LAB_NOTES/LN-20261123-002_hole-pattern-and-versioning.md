---
id: LN-20261123-002
date: 2026-11-23
timezone: Asia/Ho_Chi_Minh
status: complete
record_type: development
version: 4.0.1
---

# Kiểm quy tắc lỗ và bắt đầu quản lý source/lab note

## Objective / Mục tiêu

Trả lời lỗ có ngẫu nhiên không bằng mã nguồn hiện tại; phân biệt quy tắc hình học với tối ưu cơ học; tạo quy trình lab note cho mọi thay đổi sau này và chuẩn bị repository riêng tư mới theo lựa chọn người dùng.

## Changes / Thay đổi

- Đọc lại _tiles và build_piece trong cast_template.py; không có bộ sinh ngẫu nhiên. Số ô và các hàng/cột dành cho đai được quyết định bởi tham số.
- Không đổi thuật toán vị trí lỗ. Đổi giải thích hole_ratio trong app.py: tỷ lệ kích thước, không phải phần trăm diện tích rỗng.
- Báo cáo có trạng thái thiết kế lỗ chưa kiểm chứng cơ học; minimum ligament và open area fraction để null; chưa có anatomical exclusion masks.
- Thêm docs/PERFORATION_DESIGN.md, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md, template/ghi chú LAB_NOTES, .gitignore, hook tùy chọn và hai script tạo/kiểm note.
- Thêm test tái lập hình học từ cùng đầu vào và các test cho việc tạo/kiểm note.
- Baseline và các kết quả cũ được ghi riêng ở LN-20261123-001 theo dạng hồi cứu.

## Validation / Kiểm tra

Đã chạy trong Linux/Python 3.12.14:

- QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v: 90 test qua trong 16.474 giây (chạy lại sau sửa helper).
- node tests/check_viewer.cjs demo_export/XEM_MAU_3D.html: 7.264 tam giác khi bật hai mảnh, 3.632 khi còn một mảnh; toggle/rotate/zoom/reset qua trong harness. Chưa phải kiểm trình duyệt thật.
- Test mới tái lập cùng đầu vào: tọa độ và faces của hai vỏ trùng trong dung sai 1e-9 mm.
- Test note: chặn source thiếu note, note draft, README giả làm note; nhận record complete đúng mục và không ghi đè khi tạo hai note. Thêm test gọi checker từ ngoài thư mục repository.
- Bằng chứng: verification/lab_unittest_20261123.log.

Một lần gọi checker từ thư mục cha thất bại vì Git chạy sai thư mục. Đã sửa helper neo vào project root và thêm integration test; kiểm lại đã qua.

Kiểm python tools/check_lab_notes.py --staged đã qua sau khi git init và stage source/note. Chưa in hay chạy Fusion.

Xuất bản GitHub chưa thực hiện: trang đăng nhập trả Incorrect username or password. Chỉ ghi trạng thái, không lưu thông tin đăng nhập. GITHUB_SETUP.md giữ bước tiếp tục; không đẩy source sang repository khác.

## Limitations / Giới hạn

Các phép kiểm topology và tái lập không chứng minh độ bền. Chưa đo bề rộng vách theo mm, độ thoáng thực, nhiệt/ẩm, tải đứt, áp lực, tự giao toàn bộ hoặc hiệu quả lâm sàng. Chưa có scan người dùng hay mẫu in; chưa thử Windows/Fusion trực tiếp.
Hook chỉ kiểm có note đúng định dạng, không xác minh tính đúng của bằng chứng. Ghi chép thí nghiệm do người dùng làm cần số liệu/ảnh/lệnh thực tế.
Các bản export v4 trong demo_export được giữ để truy vết, không gắn nhãn đã dựng lại bằng v4.0.1.

## Next / Bước tiếp

Hoàn tất lưu source lên repository riêng tư khi đăng nhập tạo repo xong. Bước phát triển kỹ thuật tiếp theo đề xuất: đo vách lỗ–lỗ/lỗ–mép trên hình học thực, sau đó thiết kế phép thử cơ học trên mô hình/gá. Chưa tự triển khai tối ưu topology hoặc chọn ngưỡng điều trị.

Nguồn đã đối chiếu được liệt kê trong docs/PERFORATION_DESIGN.md; không gọi pattern hiện tại là bản sao nghiên cứu hoặc sản phẩm thương mại.
