Tạo một script bash để tự động cài đặt môi trường cho hệ thống này trên Ubuntu 22.04.

setup_ubuntu.sh
chmod +x setup_ubuntu.sh
Để sử dụng script này:

Tải script lên máy chủ Ubuntu
Chạy lệnh:
sudo ./setup_ubuntu.sh
Script sẽ:

Cài đặt Python, PostgreSQL, Nginx và các gói phụ thuộc
Tạo CSDL và tài khoản PostgreSQL
Cấu hình Nginx làm reverse proxy
Tạo service systemd để chạy ứng dụng
Lưu thông tin tài khoản vào system_accounts.txt
Sau khi chạy xong, ứng dụng sẽ:

Chạy trên cổng 5000 (internal)
Được Nginx proxy qua cổng 80 (public)
Tự động khởi động khi server reboot
Sử dụng PostgreSQL thay vì SQLite
