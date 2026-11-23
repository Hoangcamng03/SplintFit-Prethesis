---
id: LN-20261124-003
date: 2026-11-24
timezone: Asia/Ho_Chi_Minh
status: complete
record_type: development
---

# Tạo repository riêng tư và nhập source

## Objective / Mục tiêu

Sau khi người dùng hoàn tất đăng nhập, tạo repository riêng tư mới để lưu source và lab notes.

## Changes / Thay đổi

Đã tạo Hoangcamng03/SplintFit-Prethesis với visibility Private và README khởi tạo.
Cập nhật GITHUB_SETUP.md từ hướng dẫn chờ tạo repo sang cách clone repository đã có; nhập snapshot source v4.0.1, hàm tạo dữ liệu mô phỏng, tài liệu và bằng chứng kiểm thử. Mesh, ảnh preview và HTML có nhúng hình học không được đưa lên repository.
Không đổi thuật toán hình học, thư viện, giá trị mặc định hoặc giao diện app trong lần này.

## Validation / Kiểm tra

Quan sát trang GitHub hiển thị repository và nhãn Private. Connector trả visibility private, tài khoản owner Hoangcamng03 và quyền push/admin.
Source được nhập từ thư mục đã kiểm v4.0.1. Giữ bằng chứng 90/90 kiểm thử ở note LN-20261123-002, không ghi thành lần thử mới ngày 24/11.
Kiểm định dạng lab note/staged trước nhập. Việc push và đối chiếu cây file được xác minh riêng khi hoàn tất tác vụ; note này không tự chứng nhận việc đồng bộ từng byte.

## Limitations / Giới hạn

Đây là snapshot nhập ban đầu, không phải lịch sử đầy đủ của mọi bản MVP trước đó. Note cũ ghi đăng nhập thất bại vẫn giữ nguyên như sự kiện lịch sử.
Chưa có CI, thử Windows/Fusion trực tiếp, mẫu in, kiểm cơ học hoặc lâm sàng mới.

## Next / Bước tiếp

Các lần sửa sau thêm lab note cùng commit. Clone repository trên máy của người dùng, bật hook tùy chọn theo CONTRIBUTING.md và thử luồng app–Fusion với mẫu tổng hợp trước.

## Import scope adjustment

Auto-review rejected an STL blob upload because scan-derived geometry was not separately authorized. Continued with source, documents and test logs only. Excluded demo_export geometry/HTML, sample geometry and preview image from this import. No alternate encoding or upload route is used for the rejected artifacts. Synthetic examples remain reproducible from hand_demo_mesh and demo_mesh in source.
