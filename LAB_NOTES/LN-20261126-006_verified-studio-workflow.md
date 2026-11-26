---
id: LN-20261126-006
date: 2026-11-26
timezone: Asia/Ho_Chi_Minh
status: complete
record_type: development-and-reproduction
---

# Rà soát Studio và kiểm luồng bằng scan công khai

## Objective / Mục tiêu

Theo yêu cầu người dùng: chỉnh app và tài liệu để dễ hiểu, tìm scan cánh tay có nguồn để kiểm luồng. Kế thừa studio-v2 tại fc89a8d3470146a7f0d4637a8879cf4fed23dab4; làm trên codex/studio-verified-workflow, không ghi đè main/studio-v2 của agent khác.

## Changes / Thay đổi

- frontend/index.html, frontend/app.js: bộ thử A/B/C thay nhãn lâm sàng, giải thích chừa + đệm, tách độ dày với độ cứng; khuyết mặc định 0; hiển thị khoảng cách lấy mẫu riêng.
- Gợi ý hình học được ghi đúng giới hạn, cảnh báo fallback, thêm đảo hai đầu; xác nhận tỷ lệ/vùng. Đổi đơn vị cần nạp lại, đổi mốc cần xác nhận lại.
- Đổi thông số xóa hình/xuất cũ; chặn thao tác chồng khi đang xử lý. Chặn qua bước xuất nếu chưa dựng mô hình hiện tại. Khi ghi thư mục trình duyệt lỗi, giữ ZIP server làm đường lấy kết quả và không báo đã lưu đủ.
- backend/server.py: version thống nhất 2.1.0-research; validation scale/số hữu hạn/boolean/JSON; build thất bại hoặc đổi mảnh xóa cache cũ; export yêu cầu build ID và thông số trùng; sửa kiểm đường dẫn tải file thoát thư mục; timestamp microsecond tránh đụng tên.
- engine/geometry.py: gợi ý có nhãn SAMPLED_GEOMETRY_ONLY/FALLBACK_NOT_VERIFIED, không tự nhận diện giải phẫu. engine/cast_template.py sửa lời mô tả loe mép, không thay thuật toán dựng lưới trong lần này.
- requirements.txt, START_STUDIO.bat, launch_studio.py: bỏ đường Python cá nhân; tạo venv/cài dependencies; đợi health rồi mở trình duyệt, giữ console và dừng tiến trình con.
- frontend/guide.html, README.md, docs/TEST_PROTOCOL.md, docs/TEST_RESULTS.md: luồng cho người mới, nguồn từng thông số, hướng dẫn Fusion và giới hạn.
- LABNOTE.md: thêm phần đính chính, giữ nguyên lịch sử agent trước. Chưa xác nhận lại file Hand and Forearm - Full.stl của agent trước.
- tools/check_public_scan.py và tests bổ sung ca tái hiện, lỗi dữ liệu và xuất cũ. verification chứa log và số liệu, không chứa scan/mesh/ảnh nguồn.

## Validation / Kiểm tra

Môi trường Linux/Python 3.12; dependencies cụ thể ở docs/TEST_RESULTS.md.

1. Baseline: 2/2 test Studio API qua trong 2,055 giây; không phải bộ 90 test Qt.
2. Bản rà soát: python -m unittest discover -s tests -v: **10/10 qua, 11,552 giây** ở lần cuối; log verification/unittest_20261126.txt. Kiểm chặn scale sai, dữ liệu boolean/số, xác nhận scan ngoài, build thất bại/xuất cũ, đổi mảnh lỗi, mất tam giác và đường dẫn prefix-sibling.
3. node tests/test_frontend_workflow.cjs: qua trạng thái/điều hướng/khóa tác vụ/xuất cũ và fallback ZIP khi ghi thư mục bị từ chối; đây là DOM adapter, không phải trình duyệt thật. node --input-type=module --check < frontend/app.js qua.
4. Tìm/tải UW GRAIL Arm Scan Data: https://grail.cs.washington.edu/data/scans/. Cho phép nghiên cứu phi thương mại và ghi công University of Washington Graphics and Imaging Laboratory, Brett Allen/Brian Curless/Zoran Popović. 001.obj, 94.795 tam giác sau clean; không vá lỗ. Hash nguồn ở TEST_RESULTS và verification/public_scan_summary_20261126.json.
5. tools/check_public_scan.py --data-dir <ngoài Git>: ba cấu hình trên ROI chọn tay dài 206 mm. Cả ba dựng, xuất hai gói, tải từng file/ZIP và đọc lại OBJ/STL qua. Bốn OBJ/gói có mặt 4 đỉnh, STL mỗi mảnh kín theo cạnh, không non-manifold/suy biến; scan giữ bounds trong .001 đơn vị thử.
6. Chạy server thật bằng subprocess trên 127.0.0.1:8766, gọi HTTP multipart upload → build → export → download ZIP với UW001: HTTP 200, 5 file, length 206 mm. Không thay bằng thao tác trong GUI.
7. Xóa một tam giác nguồn trong ROI: HTTP 422, giữ nguyên nguyên tắc không vá và xóa kết quả cũ.
8. Kiểm cú pháp Python/JS, HTML ID/liên kết và diff trước đưa source lên GitHub. Không chạy lại hình học sau thay đổi chỉ văn bản.

Lỗi trong quá trình: harness Node lần đầu thiếu PRIMARY_BTN_LABELS (ReferenceError); đã nạp đúng khối hàm/constants từ source và kiểm lại qua. Trình duyệt của phiên không truy cập localhost của môi trường (connection refused/policy gate); dừng thử browser, không dùng cách vòng qua. Vì vậy chưa kiểm WebGL/bố cục/native directory dialog.

### Phát hiện định lượng cần theo dõi

- Gợi ý tự động trên scan toàn cánh tay dài khoảng 536,5 mm và bao gồm phần trên khuỷu; tự động qua kiểm hình học không đồng nghĩa đúng vùng giải phẫu. Ca thử đã thu vùng trước khi dựng.
- Khoảng chừa danh nghĩa B/A/C là 2,0 / 3,5 / 1,3 mm, nhưng khoảng cách không dấu nhỏ nhất ở mẫu kiểm là 0,778 / 2,044 / 0,081 mm. Không phát hiện điểm trong thành ở mẫu kiểm không có nghĩa đủ khoảng chừa hoặc không giao ở nơi khác. Chưa sửa thuật toán hình học để bảo đảm khoảng cách nhỏ nhất; giao diện và báo cáo đã tách rõ hai đại lượng.

## Limitations / Giới hạn

Chỉ một scan, một tư thế, ba cấu hình. Tọa độ coi là mm theo quy ước thử, chưa có thước đối chứng hoặc ground truth lâm sàng. ROI là sleeve cẳng tay chọn để kiểm pipeline, không chứng minh bất động cổ tay.
Chưa thử launcher/GUI Windows, WebGL hoặc lưu thư mục thực. Chưa có Autodesk Fusion để Convert/Edit Form/Finish Form/Thicken; chưa có F3D, slicing, in vật lý, đệm/đai, đo độ bền/áp lực/điều trị. Không gọi toàn quy trình chế tạo PASS. Phiên bản này vẫn là prototype.
Dữ liệu nghiên cứu nguồn và geometry dẫn xuất nằm ngoài Git; chỉ đẩy code/tài liệu/log và chỉ số. Các số thử không phải chỉ định điều trị hoặc tiêu chí nghiệm thu thesis.

## Next / Bước tiếp

Đối chiếu thay đổi của agent khác trước khi gộp vào studio-v2. Thử GUI/launcher Windows và hướng dẫn từng bước trên máy người dùng. Thử Fusion bằng OBJ nền trước, ghi F3D/kết quả và sai lệch. Ưu tiên kiểm độ chính xác mặt cong và khoảng cách nhỏ nhất trước khi tăng tính năng; sau đó xây protocol nhiều scan/in trên mô hình, chốt tiêu chí với giảng viên.
