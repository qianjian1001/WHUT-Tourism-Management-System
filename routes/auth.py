from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'customer')

        user = User.query.filter_by(username=username, role=role).first()
        if user and user.check_password(password):
            login_user(user)
            flash('登录成功！', 'success')
            if user.is_staff:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('customer.dashboard'))
        flash('用户名或密码错误，或角色不匹配。', 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('用户名已存在。', 'danger')
            return render_template('register.html')

        user = User(username=username, name=name, phone=phone, email=email, role='customer')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已安全退出。', 'info')
    return redirect(url_for('auth.login'))
