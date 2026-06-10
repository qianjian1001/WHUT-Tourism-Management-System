# 途行旅行社管理系统

基于 Flask 的旅行社业务管理平台，支持旅游路线管理、旅行团发布、客户预订、财务对账等全流程操作。内置管理员、员工、客户三种角色，界面采用 Apple 风格设计。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python Flask 3.0 |
| ORM | Flask-SQLAlchemy 3.1 |
| 认证 | Flask-Login + Werkzeug 密码哈希 |
| 数据库 | SQLite |
| 前端 | Jinja2 模板 + Tailwind CSS (CDN) |
| UI 风格 | 毛玻璃效果、渐变、Apple 风格组件 |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库（含示例数据）
python init_db.py

# 3. 启动服务
python app.py
```

访问 `http://localhost:5000`

### 默认账户

| 账户 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 管理员 |
| staff | staff123 | 员工 |
| customer | 123456 | 客户 |

## 功能概览

### 管理端 (`/admin`)

- **仪表盘** — 运营数据概览，即将到期款项提醒
- **路线管理** — 旅游路线的增删改查，启用/停用，变更历史追溯
- **旅行团管理** — 创建出发团次，设定价格与容量，发布/取消
- **预订管理** — 查看所有订单，确认定金/尾款，处理取消退款
- **参与者管理** — 添加/取消参团人员，转移申请人
- **文档生成** — 按日导出确认订单清单
- **财务报告** — 导出未导出付款记录，标记已导出

### 客户端 (`/customer`)

- **浏览旅行团** — 按条件筛选可报名旅行团
- **在线预订** — 填写参团信息，自动计算定金
- **我的订单** — 查看预订详情、付款状态、取消信息
- **个人中心** — 修改资料与密码

## 项目结构

```
travel/
├── app.py                  # Flask 应用入口
├── config.py               # 配置文件
├── models.py               # 数据模型（9 张表）
├── init_db.py              # 数据库初始化 + 种子数据
├── requirements.txt        # Python 依赖
├── travel.db               # SQLite 数据库
├── routes/
│   ├── auth.py             # 认证（登录/注册/登出）
│   ├── admin.py            # 管理端路由
│   └── customer.py         # 客户路由
├── templates/
│   ├── base.html           # 基础布局
│   ├── admin/              # 管理端模板
│   └── customer/           # 客户模板
└── static/
    ├── css/style.css       # 自定义样式
    └── js/main.js          # 前端交互
```

## 数据模型

- **User** — 用户（admin / staff / customer）
- **TourRoute** — 旅游路线（目的地、行程天数）
- **RouteHistory** — 路线变更审计日志
- **TourGroup** — 旅行团（出发日期、价格、名额）
- **PriceHistory** — 定价变更审计日志
- **Booking** — 预订（定金、尾款、状态）
- **Participant** — 参团人员（成人/儿童）
- **Payment** — 付款记录（定金/尾款/退款）
- **Cancellation** — 取消记录（违约金自动计算）

## 违约金规则

距出发天数越近，违约金比例越高：

| 距出发天数 | 违约金比例 |
|-----------|-----------|
| ≥ 30 天 | 10% |
| ≥ 20 天 | 20% |
| ≥ 10 天 | 30% |
| ≥ 2 天 | 50% |
| < 2 天 | 100% |
