from app import create_app
from models import db, User, TourRoute, TourGroup
from datetime import date, timedelta

app = create_app()

with app.app_context():
    db.create_all()

    # Create admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', name='系统管理员', role='admin', phone='13800000000')
        admin.set_password('admin123')
        db.session.add(admin)

    # Create staff user
    if not User.query.filter_by(username='staff').first():
        staff = User(username='staff', name='张员工', role='staff', phone='13800000001')
        staff.set_password('staff123')
        db.session.add(staff)

    # Create sample customer
    if not User.query.filter_by(username='customer').first():
        customer = User(username='customer', name='李客户', role='customer', phone='13900000000')
        customer.set_password('123456')
        db.session.add(customer)

    # Create sample tour routes
    if TourRoute.query.count() == 0:
        routes_data = [
            {'code': 'RT001', 'name': '丽江古城3日游', 'destination': '云南丽江', 'description': '游览丽江古城、玉龙雪山、束河古镇等著名景点', 'duration_days': 3},
            {'code': 'RT002', 'name': '三亚海滨度假5日游', 'destination': '海南三亚', 'description': '享受阳光沙滩、潜水体验、海岛游', 'duration_days': 5},
            {'code': 'RT003', 'name': '西安历史文化4日游', 'destination': '陕西西安', 'description': '参观兵马俑、大雁塔、古城墙等历史遗迹', 'duration_days': 4},
            {'code': 'RT004', 'name': '张家界自然风光4日游', 'destination': '湖南张家界', 'description': '探索袁家界、天门山、玻璃栈道', 'duration_days': 4},
            {'code': 'RT005', 'name': '成都美食熊猫3日游', 'destination': '四川成都', 'description': '品尝美食、熊猫基地、宽窄巷子', 'duration_days': 3},
            {'code': 'RT006', 'name': '桂林漓江山水4日游', 'destination': '广西桂林', 'description': '漓江竹筏、阳朔西街、龙脊梯田', 'duration_days': 4},
            {'code': 'RT007', 'name': '北京古都文化5日游', 'destination': '北京', 'description': '故宫、长城、天坛、颐和园', 'duration_days': 5},
        ]
        for r in routes_data:
            db.session.add(TourRoute(**r, created_by=1))

    # Create sample tour groups
    if TourGroup.query.count() == 0:
        today = date.today()
        groups_data = [
            {
                'code': 'TG20240601', 'route_id': 1, 'departure_date': today + timedelta(days=25),
                'return_date': today + timedelta(days=28), 'deadline_date': today + timedelta(days=20),
                'max_participants': 30, 'current_participants': 8,
                'adult_price': 2800, 'child_price': 1400,
                'discount_info': '早鸟优惠：提前15天报名减200元/人', 'price_published': True,
                'status': 'published', 'created_by': 1
            },
            {
                'code': 'TG20240602', 'route_id': 2, 'departure_date': today + timedelta(days=35),
                'return_date': today + timedelta(days=40), 'deadline_date': today + timedelta(days=28),
                'max_participants': 25, 'current_participants': 12,
                'adult_price': 4800, 'child_price': 2400,
                'discount_info': '家庭套餐：2大1小减500元', 'price_published': True,
                'status': 'published', 'created_by': 1
            },
            {
                'code': 'TG20240603', 'route_id': 3, 'departure_date': today + timedelta(days=15),
                'return_date': today + timedelta(days=19), 'deadline_date': today + timedelta(days=10),
                'max_participants': 35, 'current_participants': 20,
                'adult_price': 3200, 'child_price': 1600,
                'discount_info': '', 'price_published': True,
                'status': 'published', 'created_by': 1
            },
            {
                'code': 'TG20240604', 'route_id': 4, 'departure_date': today + timedelta(days=45),
                'return_date': today + timedelta(days=49), 'deadline_date': today + timedelta(days=38),
                'max_participants': 20, 'current_participants': 5,
                'adult_price': 3500, 'child_price': 1750,
                'discount_info': '早鸟优惠：提前30天报名减300元', 'price_published': True,
                'status': 'published', 'created_by': 1
            },
            {
                'code': 'TG20240605', 'route_id': 5, 'departure_date': today + timedelta(days=20),
                'return_date': today + timedelta(days=23), 'deadline_date': today + timedelta(days=14),
                'max_participants': 25, 'current_participants': 15,
                'adult_price': 2200, 'child_price': 1100,
                'discount_info': '', 'price_published': True,
                'status': 'published', 'created_by': 1
            },
            {
                'code': 'TG20240606', 'route_id': 6, 'departure_date': today + timedelta(days=60),
                'return_date': today + timedelta(days=64), 'deadline_date': today + timedelta(days=50),
                'max_participants': 30, 'current_participants': 0,
                'adult_price': 3800, 'child_price': 1900,
                'discount_info': '', 'price_published': False,
                'status': 'draft', 'created_by': 1
            },
        ]
        for g in groups_data:
            db.session.add(TourGroup(**g))

    db.session.commit()
    print("数据库初始化完成！")
    print("管理员账户: admin / admin123")
    print("员工账户: staff / staff123")
    print("客户账户: customer / 123456")
