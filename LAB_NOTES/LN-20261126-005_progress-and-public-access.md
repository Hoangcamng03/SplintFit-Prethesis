---
id: LN-20261126-005
date: 2026-11-26
timezone: Asia/Ho_Chi_Minh
status: complete
record_type: documentation-review
---

# Cập nhật tiến trình, quyền Public và nhu cầu người dùng

## Objective / Mục tiêu

Theo yêu cầu chủ dự án, tổng hợp tiến trình dựa trên lab notes hiện có trên GitHub và cập nhật trạng thái sau chuyển Public. Phân biệt công việc đã làm, bằng chứng cũ, yêu cầu mới và kế hoạch.

## Changes / Thay đổi

- Thêm docs/PROJECT_PROGRESS.md: các mốc 20/11–26/11, trạng thái chức năng, nhu cầu thesis và các bước tiếp theo.
- README.md thêm lối vào tiến trình và trạng thái Public; làm rõ gói demo trong ZIP baseline không nằm trong repository source.
- LAB_NOTES/README.md sửa bảng chỉ mục bị ngắt, liên kết các note và bổ sung LN-005.
- Ghi chuyển Private → Public ngày 26/11/2026 theo xác nhận người dùng trong hội thoại. Giữ nguyên note cũ vì Private là trạng thái lịch sử đúng tại thời điểm đó.
- Ghi yêu cầu giao diện dễ hiểu và thông tin có giảng viên/máy in/vật liệu lab theo lời người dùng. Không coi yêu cầu là tính năng đã triển khai.
- Không sửa code, hình học, dependencies hoặc nâng phiên bản phần mềm.

## Validation / Kiểm tra

- Đọc trực tiếp AGENTS.md, README.md, CHANGELOG.md, TEST_RESULTS.md, template và bốn lab note trên GitHub trước cập nhật.
- GitHub get_repo xác nhận visibility public ngày 26/11/2026. Trước cập nhật, main ở commit 7a2f9d77ca8531d56f2e9a2dea2b2ed61994ac36.
- Đối chiếu kết quả 83 test baseline (20/11) và 90/90 test v4.0.1 (23/11) với note tương ứng; không chạy lại hoặc đổi ngày kết quả.
- Kiểm định dạng note, tính nhất quán mốc và liên kết nội bộ trước commit. Không chạy lại test hình học vì chỉ sửa tài liệu.
- Sau khi đưa lên GitHub, cần đọc lại các file đã đổi để đối chiếu đúng nội dung; kết quả xác minh xuất bản được báo riêng sau thao tác.

## Limitations / Giới hạn

Chưa có bằng chứng mới về Windows, Fusion, scan người dùng, in vật lý, cơ học, áp lực hoặc lâm sàng. Chưa chốt tiêu chí “sản phẩm hoàn thiện” cho thesis. Bản cập nhật không phải bản cải tiến UI/engine.
Các chi tiết máy/vật liệu và hỗ trợ chuyên môn cần xác nhận; không công khai dữ liệu định danh hoặc scan người thật.

## Next / Bước tiếp

Chốt phạm vi và tiêu chí với giảng viên; ghi ca mẫu Windows → Fusion; dùng kết quả để ưu tiên UI dễ hiểu, sau đó kiểm scan và in trên mô hình/gá. Mỗi thay đổi có lab note và bằng chứng phù hợp.
