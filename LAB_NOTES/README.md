# Nhật ký phát triển và thực nghiệm

Mỗi nhóm thay đổi có ý nghĩa cần một note cùng commit. Tên: LN-YYYYMMDD-NNN_slug.md, ngày Việt Nam. Không tạo hàng chục note cho từng phím gõ; gom thay đổi cùng mục tiêu và phép kiểm.

1. Trước khi sửa: python tools/new_lab_note.py "Ten thay doi".
2. Ghi mục tiêu, giả thuyết, dữ liệu và tham số dự kiến.
3. Sau khi sửa/thử: ghi thay đổi thực tế, lệnh và kết quả, kể cả thất bại.
4. Ghi rõ phần chưa kiểm chứng; chuyển status từ draft thành complete khi bản ghi đủ nội dung.
5. Stage source và note, rồi chạy python tools/check_lab_notes.py --staged trước commit.

Complete chỉ nghĩa là ghi chép xong. Nó không phải nhãn thiết bị đạt độ bền hoặc an toàn.

Ghi chép hồi cứu phải có record_type: retrospective và nguồn xác minh. Không sửa ngày của note để giả làm bản ghi tại thời điểm thí nghiệm. Nếu sửa kết luận cũ, thêm phần bổ sung có ngày/lý do hoặc note đính chính mới.

Lab note không tự sinh bằng chứng. Script chỉ hỗ trợ tạo khung và kiểm định dạng. Sau thao tác Fusion, scan hoặc in do bạn thực hiện, cần bổ sung dữ liệu quan sát; tôi không thể ghi đó là đã thử nếu bạn chưa cung cấp kết quả.

| Note | Nội dung |
|---|---|
| LN-20261123-001 | Hồi cứu baseline v4 đã cung cấp 20/11/2026 |
| LN-20261123-002 | Kiểm quy tắc lỗ, bổ sung quản lý phiên bản và lab note |

| LN-20261124-003 | Tạo repository riêng tư và nhập source |
