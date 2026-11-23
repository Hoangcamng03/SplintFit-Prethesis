# Cách lưu source và thay đổi

## Một lần thay đổi

1. Tạo nhánh theo mục tiêu, ví dụ git switch -c feature/hole-web-metrics.
2. Tạo note: python tools/new_lab_note.py "Measure minimum ligament".
3. Sửa source; ghi tham số và căn cứ trong note.
4. Chạy kiểm thử phù hợp. Ghi chính xác lệnh/kết quả và điều chưa kiểm trong note.
5. Chuyển status của note sang complete khi ghi chép đủ.
6. git add các file cần lưu và note.
7. python tools/check_lab_notes.py --staged.
8. git commit -m "Describe the resulting behavior" rồi git push.

Cài hook cục bộ nếu muốn kiểm note trước mỗi commit:

    git config core.hooksPath .githooks

Git không bật hook tự động sau clone; đây là cấu hình cho máy đang dùng. Hook chỉ kiểm sự hiện diện/định dạng note, không chứng minh nội dung khoa học đúng và không thể ngăn mọi cách bypass. AGENTS.md ghi yêu cầu cho các lần làm việc tiếp theo.

## Kiểm thử

    python -m unittest discover -s tests -v
    node tests/check_viewer.cjs demo_export/XEM_MAU_3D.html

Node chỉ cần cho harness viewer, không cần để chạy app.
Windows/Fusion và in thật phải có bản ghi thử riêng, không suy ra từ unit test.

## Dữ liệu

Chỉ lưu dữ liệu tổng hợp đã đánh dấu. Scan người thật, hồ sơ định danh, token và môi trường .venv không thuộc repository mặc định. .gitignore là lớp hỗ trợ, không thay việc xem danh sách file trước push.

## Phiên bản

README.md ghi cách chạy; CHANGELOG.md ghi thay đổi hành vi theo phiên bản; LAB_NOTES giữ lý do/bằng chứng/giới hạn; Git giữ diff source. Gắn mã note vào mô tả commit/PR khi phù hợp.
