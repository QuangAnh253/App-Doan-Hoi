# Hệ Thống Quản Lý Đoàn - Hội

[English](README.en.md) | [中文](README.zh.md) | **Tiếng Việt**

## Thông Tin Dự Án

**Phiên bản hiện tại:** 2.0.0  
**Tác giả:** Lê Quang Anh  
**Đơn vị:** Ban Văn phòng - Hội Sinh viên  
**Tình trạng:** Phát triển nội bộ (Internal Development)

## Mô Tả

Hệ thống quản lý công tác Đoàn - Hội là giải pháp chuyển đổi số được xây dựng nhằm mục đích chuẩn hóa quy trình quản lý dữ liệu và nghiệp vụ công tác Hội tại đơn vị. Phần mềm hỗ trợ quản lý hồ sơ sinh viên, theo dõi nhân sự cán bộ lớp và điều hành các hoạt động nội bộ.

**Lưu ý quan trọng:** Đây là phần mềm nội bộ được phát triển cho các đơn vị công tác Đoàn - Hội. Việc sử dụng ngoài phạm vi tổ chức cần được xem xét và phê duyệt.

## Tính Năng Chính

### 1. Quản lý Hồ sơ Sinh viên và Hội viên
- Số hóa toàn bộ thông tin sinh viên
- Thêm mới, cập nhật hoặc xóa dữ liệu
- Tìm kiếm và tra cứu nhanh theo MSSV, họ tên hoặc lớp
- Nhập liệu (Import) và xuất báo cáo (Export) từ file Excel
- Ghi chú đặc biệt và quản lý vị trí lưu trữ hồ sơ cứng

### 2. Quản lý Đơn vị Lớp và Cán bộ nguồn
- Quản lý danh sách các chi hội và lớp, phân loại theo Khoa và Khóa học
- Theo dõi hệ thống Ban Chấp hành và Ban Điều hành tại các chi hội
- Theo dõi nhiệm kỳ công tác, hỗ trợ thi đua khen thưởng và quy hoạch cán bộ

### 3. Tác vụ Văn phòng và Nội bộ
- Hệ thống thông báo nội bộ và chia sẻ văn bản, tài liệu điều hành
- Phân công nhiệm vụ (Giao việc) và theo dõi tiến độ thực hiện

### 4. Lưu trữ và Bảo mật dữ liệu
- Quản lý kho tài liệu số hóa và file đính kèm
- Cơ chế sao lưu (Backup) và khôi phục dữ liệu
- Ghi lại lịch sử thay đổi để phục vụ công tác kiểm tra và giám sát

## Yêu Cầu Hệ Thống

### Cấu hình tối thiểu:
- **Hệ điều hành:** Windows 10 (64-bit) trở lên
- **RAM:** 4 GB
- **Dung lượng:** 500 MB trống
- **Màn hình:** 1366x768
- **Internet:** Kết nối ổn định (bắt buộc để đồng bộ dữ liệu)

### Cấu hình khuyến nghị:
- **Hệ điều hành:** Windows 11 (64-bit)
- **RAM:** 8 GB trở lên
- **Ổ cứng:** SSD với dung lượng trống ít nhất 1 GB
- **Màn hình:** Full HD (1920x1080)

## Công Nghệ Sử Dụng

- **Python 3.x** - Ngôn ngữ lập trình chính
- **CustomTkinter** - Giao diện người dùng hiện đại
- **Supabase** - Cơ sở dữ liệu và xác thực
- **PyInstaller** - Đóng gói ứng dụng
- **Inno Setup** - Tạo bộ cài đặt Windows

## Cài Đặt

**Không khuyến nghị tự build từ mã nguồn.** Vui lòng sử dụng bộ cài đặt chính thức được cung cấp bởi đơn vị.

### Quy trình khởi chạy:
1. Mở ứng dụng "Quản Lý Đoàn - Hội" sau khi hoàn tất cài đặt
2. Đăng nhập bằng tài khoản nội bộ được cấp hoặc sử dụng liên kết xác thực qua Google/Discord
3. Chờ Quản trị viên phê duyệt để kích hoạt quyền truy cập (đối với tài khoản mới)

### Lưu ý vận hành:
- Ứng dụng cần kết nối Internet liên tục để đồng bộ dữ liệu theo thời gian thực
- Thời gian khởi động lần đầu có thể mất từ 10-15 giây để tải tài nguyên
- Khuyến nghị thường xuyên cập nhật lên phiên bản mới nhất để vá lỗi và bổ sung tính năng

Nếu cần thiết, liên hệ qua:
- **Email:** lequanganh253@gmail.com
- **Website:** https://appdoanhoi.lequanganh.id.vn

## Bảo Mật

Hệ thống tuân thủ các nguyên tắc bảo mật dữ liệu nghiêm ngặt:

- Cơ sở dữ liệu được lưu trữ trên Supabase (chuẩn bảo mật SOC 2 Type II)
- Phân cấp quyền hạn: Quản trị viên (Admin), Cán bộ (Staff), Người dùng (User)
- Mã hóa kết nối qua HTTPS/SSL
- Không lưu trữ mật khẩu dưới dạng plain text
- Ghi lại lịch sử thay đổi để phục vụ công tác kiểm tra và giám sát

## Hỗ Trợ và Liên Hệ

**Tác giả:** Lê Quang Anh  
**Email:** lequanganh253@gmail.com  
**Website:** https://lequanganh.id.vn  
**Đơn vị:** Ban Văn phòng - Hội Sinh viên

### Kênh hỗ trợ:
- **Cổng thông tin:** https://appdoanhoi.lequanganh.id.vn
- **Tài liệu hướng dẫn:** https://appdoanhoi.lequanganh.id.vn/guidelines
- **GitHub Issues:** https://github.com/QuangAnh253/App-Doan-Hoi/issues
- **Thời gian phản hồi:** 24-48 giờ

## Giấy Phép

Dự án này được cấp phép theo MIT License với các điều khoản bổ sung cho sử dụng nội bộ.

Xem chi tiết tại file [LICENSE](LICENSE.txt).

### Bản quyền
Bản quyền © 2026 Lê Quang Anh. Bảo lưu mọi quyền.

Phần mềm được phát triển cho mục đích sử dụng nội bộ tại các đơn vị công tác Đoàn - Hội. Nghiêm cấm các hành vi sao chép, phân phối hoặc sử dụng trái phép mã nguồn vào mục đích thương mại khi chưa có sự đồng ý bằng văn bản.

## Lưu Ý Quan Trọng

1. Phần mềm này được phát triển cho mục đích nội bộ
2. Việc sử dụng và phân phối cần tuân thủ các quy định của tổ chức
3. Không tự ý thay đổi hoặc phân phối lại phần mềm
4. Mọi vấn đề kỹ thuật vui lòng liên hệ qua kênh chính thức

## Changelog

### Version 2.0.0 (Hiện tại)
- Nâng cấp toàn diện giao diện người dùng
- Cải thiện hiệu suất và tốc độ xử lý
- Tăng cường bảo mật với mã hóa nâng cao
- Bổ sung tính năng sao lưu tự động
- Hỗ trợ đa ngôn ngữ (Tiếng Việt, English, 中文)
- Tối ưu hóa trải nghiệm người dùng

### Version 1.9.0
- Cập nhật giao diện người dùng
- Cải thiện hiệu suất
- Sửa lỗi bảo mật
- Bổ sung tính năng sao lưu tự động

---

**Chú ý:** Repository này được công khai nhằm mục đích minh bach và giáo dục. Việc sử dụng thương mại hoặc phân phối ngoài phạm vi tổ chức cần được phê duyệt trước.

---

*Cảm ơn các đồng chí đã tin tưởng sử dụng hệ thống.*