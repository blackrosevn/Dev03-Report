# Sample organizations
SAMPLE_ORGANIZATIONS = [
    {
        "name": "Ban Tài chính Kế toán",
        "name_en": "Finance and Accounting Department",
        "code": "BTCKT",
        "description": "Ban Tài chính Kế toán - Tập đoàn Dệt May Việt Nam",
        "parent": "VINATEX"
    },
    {
        "name": "Ban Kế hoạch Đầu tư",
        "name_en": "Planning and Investment Department",
        "code": "BKHDT",
        "description": "Ban Kế hoạch Đầu tư - Tập đoàn Dệt May Việt Nam",
        "parent": "VINATEX"
    },
    {
        "name": "Ban Sản xuất",
        "name_en": "Production Department",
        "code": "BSX",
        "description": "Ban Sản xuất - Tập đoàn Dệt May Việt Nam",
        "parent": "VINATEX"
    },
    {
        "name": "Tổng Công ty CP Dệt May Hòa Thọ",
        "name_en": "Hoa Tho Textile-Garment Joint Stock Corporation",
        "code": "HOATHO",
        "description": "Tổng Công ty CP Dệt May Hòa Thọ",
        "parent": "VINATEX"
    },
    {
        "name": "Tổng Công ty CP Dệt May Hà Nội",
        "name_en": "Hanoi Textile and Garment Joint Stock Corporation",
        "code": "HANOSIMEX",
        "description": "Tổng Công ty CP Dệt May Hà Nội",
        "parent": "VINATEX"
    },
    {
        "name": "Tổng Công ty CP Phong Phú",
        "name_en": "Phong Phu Corporation",
        "code": "PHONGPHU",
        "description": "Tổng Công ty CP Phong Phú",
        "parent": "VINATEX"
    }
]

# Sample users
SAMPLE_USERS = [
    {
        "username": "finance_admin",
        "email": "finance@vinatex.com.vn",
        "password": "finance_admin",
        "fullname": "Quản trị Ban Tài chính",
        "role": "department",
        "organization": "BTCKT"
    },
    {
        "username": "planning_admin",
        "email": "planning@vinatex.com.vn",
        "password": "planning_admin",
        "fullname": "Quản trị Ban Kế hoạch",
        "role": "department",
        "organization": "BKHDT"
    },
    {
        "username": "production_admin",
        "email": "production@vinatex.com.vn",
        "password": "production_admin",
        "fullname": "Quản trị Ban Sản xuất",
        "role": "department",
        "organization": "BSX"
    },
    {
        "username": "hoatho_admin",
        "email": "admin@hoatho.com.vn",
        "password": "hoatho_admin",
        "fullname": "Quản trị Hòa Thọ",
        "role": "unit",
        "organization": "HOATHO"
    },
    {
        "username": "hanosimex_admin",
        "email": "admin@hanosimex.com.vn",
        "password": "hanosimex_admin",
        "fullname": "Quản trị Hanosimex",
        "role": "unit",
        "organization": "HANOSIMEX"
    },
    {
        "username": "phongphu_admin",
        "email": "admin@phongphu.com.vn",
        "password": "phongphu_admin",
        "fullname": "Quản trị Phong Phú",
        "role": "unit",
        "organization": "PHONGPHU"
    }
]

# Sample report templates
SAMPLE_REPORT_TEMPLATES = [
    {
        "name": "Báo cáo tài chính hàng tháng",
        "name_en": "Monthly Financial Report",
        "description": "Báo cáo tài chính hàng tháng của đơn vị thành viên",
        "structure": {
            "sheets": [
                {
                    "name": "Tổng quan",
                    "name_en": "Overview",
                    "fields": [
                        {"name": "doanh_thu", "label": "Doanh thu", "label_en": "Revenue", "type": "number", "required": True},
                        {"name": "chi_phi", "label": "Chi phí", "label_en": "Expenses", "type": "number", "required": True},
                        {"name": "loi_nhuan", "label": "Lợi nhuận", "label_en": "Profit", "type": "number", "required": True},
                        {"name": "ghi_chu", "label": "Ghi chú", "label_en": "Notes", "type": "text", "required": False}
                    ]
                },
                {
                    "name": "Chi tiết",
                    "name_en": "Details",
                    "fields": [
                        {"name": "doanh_thu_noi_dia", "label": "Doanh thu nội địa", "label_en": "Domestic Revenue", "type": "number", "required": True},
                        {"name": "doanh_thu_xuat_khau", "label": "Doanh thu xuất khẩu", "label_en": "Export Revenue", "type": "number", "required": True},
                        {"name": "chi_phi_nguyen_lieu", "label": "Chi phí nguyên liệu", "label_en": "Material Costs", "type": "number", "required": True},
                        {"name": "chi_phi_nhan_cong", "label": "Chi phí nhân công", "label_en": "Labor Costs", "type": "number", "required": True},
                        {"name": "chi_phi_khac", "label": "Chi phí khác", "label_en": "Other Costs", "type": "number", "required": True}
                    ]
                }
            ]
        }
    },
    {
        "name": "Báo cáo sản xuất hàng tháng",
        "name_en": "Monthly Production Report",
        "description": "Báo cáo sản xuất hàng tháng của đơn vị thành viên",
        "structure": {
            "sheets": [
                {
                    "name": "Sản lượng",
                    "name_en": "Production Volume",
                    "fields": [
                        {"name": "san_luong_soi", "label": "Sản lượng sợi (tấn)", "label_en": "Yarn Production (tons)", "type": "number", "required": True},
                        {"name": "san_luong_vai", "label": "Sản lượng vải (m²)", "label_en": "Fabric Production (m²)", "type": "number", "required": True},
                        {"name": "san_luong_may_mac", "label": "Sản lượng may mặc (chiếc)", "label_en": "Garment Production (pieces)", "type": "number", "required": True}
                    ]
                },
                {
                    "name": "Chất lượng",
                    "name_en": "Quality",
                    "fields": [
                        {"name": "ty_le_loi", "label": "Tỷ lệ lỗi (%)", "label_en": "Defect Rate (%)", "type": "number", "required": True},
                        {"name": "san_pham_dat", "label": "Sản phẩm đạt (%)", "label_en": "Passing Products (%)", "type": "number", "required": True},
                        {"name": "ghi_chu_chat_luong", "label": "Ghi chú về chất lượng", "label_en": "Quality Notes", "type": "text", "required": False}
                    ]
                }
            ]
        }
    },
    {
        "name": "Báo cáo kế hoạch đầu tư",
        "name_en": "Investment Plan Report",
        "description": "Báo cáo kế hoạch đầu tư của đơn vị thành viên",
        "structure": {
            "sheets": [
                {
                    "name": "Kế hoạch",
                    "name_en": "Plan",
                    "fields": [
                        {"name": "ten_du_an", "label": "Tên dự án", "label_en": "Project Name", "type": "text", "required": True},
                        {"name": "tong_von", "label": "Tổng vốn đầu tư (VNĐ)", "label_en": "Total Investment (VND)", "type": "number", "required": True},
                        {"name": "thoi_gian_bat_dau", "label": "Thời gian bắt đầu", "label_en": "Start Time", "type": "date", "required": True},
                        {"name": "thoi_gian_hoan_thanh", "label": "Thời gian hoàn thành", "label_en": "Completion Time", "type": "date", "required": True},
                        {"name": "ghi_chu", "label": "Ghi chú", "label_en": "Notes", "type": "text", "required": False}
                    ]
                },
                {
                    "name": "Tiến độ",
                    "name_en": "Progress",
                    "fields": [
                        {"name": "tien_do_giai_ngan", "label": "Tiến độ giải ngân (%)", "label_en": "Disbursement Progress (%)", "type": "number", "required": True},
                        {"name": "von_da_giai_ngan", "label": "Vốn đã giải ngân (VNĐ)", "label_en": "Disbursed Capital (VND)", "type": "number", "required": True},
                        {"name": "tien_do_thuc_hien", "label": "Tiến độ thực hiện dự án (%)", "label_en": "Project Implementation Progress (%)", "type": "number", "required": True},
                        {"name": "kho_khan_vuong_mac", "label": "Khó khăn, vướng mắc", "label_en": "Difficulties and Obstacles", "type": "text", "required": False}
                    ]
                }
            ]
        }
    }
]

# Default system settings
DEFAULT_SETTINGS = {
    "sharepoint_url": "https://vinatex.sharepoint.com/sites/reports",
    "email_notifications": "True",
    "email_reminder_days": "7,3,1",
    "smtp_server": "smtp.office365.com",
    "smtp_port": "587",
    "smtp_username": "reports@vinatex.com.vn",
    "smtp_password": "",
    "language": "vi"
}
