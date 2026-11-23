# Repository riêng tư đã tạo

https://github.com/Hoangcamng03/SplintFit-Prethesis

## Lấy source trên máy Windows

    git clone https://github.com/Hoangcamng03/SplintFit-Prethesis.git
    cd SplintFit-Prethesis

Đăng nhập GitHub trên máy nếu Git yêu cầu quyền truy cập repository private. Sau đó mở START_WINDOWS.bat hoặc đọc BAT_DAU_O_DAY.md.

## Ghi nhận thay đổi

    git config core.hooksPath .githooks
    python tools/new_lab_note.py "Ten thay doi"

Điền bằng chứng thực tế, chuyển note sang complete, stage source và note, chạy tools/check_lab_notes.py --staged rồi commit/push. Hook chỉ kiểm định dạng, không chứng minh kết quả nghiên cứu.

Xem CONTRIBUTING.md và LAB_NOTES. Không đưa scan người thật hoặc thông tin đăng nhập lên repo mặc định.
