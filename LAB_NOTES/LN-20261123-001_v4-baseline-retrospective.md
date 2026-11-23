---
id: LN-20261123-001
date: 2026-11-23
timezone: Asia/Ho_Chi_Minh
status: complete
record_type: retrospective
event_date: 2026-11-20
---

# Baseline v4 — bản ghi hồi cứu, không phải ghi tại ngày làm thí nghiệm

## Objective / Mục tiêu

Ghi lại trạng thái baseline trước khi áp dụng yêu cầu lab note cho từng thay đổi.
Nguồn: SplintFit_Cast_Prototype_v4.zip, 1.331.933 byte.
SHA-256: bf5d1295cf41dc72818e21ebeba68d97bc83828b5d41bfe50f6d28880025b4ed.

## Changes / Thay đổi

Baseline có app desktop Qt/PyVista, engine fit mặt cắt một vòng hướng tâm, hai mảnh vỏ có lỗ và khe đai, hai loại OBJ quad, STL, JSON và viewer offline.
Đây là snapshot được nhập để bắt đầu theo dõi phiên bản; không tuyên bố có lịch sử Git đầy đủ của các bản MVP cũ.

## Validation / Kiểm tra

Bằng chứng có sẵn trong TEST_RESULTS.md và verification/unittest.log của ZIP: 83 kiểm thử Python qua ngày 20/11, mẫu tổng hợp 24 lỗ thoáng, 12 khe đai, 7.264 tam giác trên hai mảnh, không có cạnh hở/non-manifold/suy biến tại phép kiểm topology.
Ảnh PREVIEW_DEMO.png được dựng từ STL tổng hợp. Viewer có Node DOM/canvas harness; không coi đó là kiểm trình duyệt thật.
Các kết quả này được trích từ hồ sơ baseline, không tự ghi thành thí nghiệm mới ngày 23/11.

## Limitations / Giới hạn

Chưa có scan người dùng, chưa in vật lý, chưa thử Windows/Fusion trực tiếp, chưa đo áp lực/độ bền hoặc kiểm định lâm sàng. Các kiểm topology và va chạm lấy mẫu không chứng minh độ bền.
Không có dữ liệu để khôi phục chính xác từng sửa đổi trước v4; không tạo commit hoặc thời gian giả cho phần đó.

## Next / Bước tiếp

Kiểm tra nguyên tắc lỗ và công khai giới hạn trong note LN-20261123-002. Từ mốc này ghi note cùng mỗi nhóm thay đổi.
