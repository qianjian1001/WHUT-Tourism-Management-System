from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, TourRoute, TourGroup, Booking, Participant, Payment, Cancellation, User
from datetime import datetime, date, timedelta

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/')
@login_required
def dashboard():
    my_bookings = Booking.query.filter_by(customer_id=current_user.id) \
                     .order_by(Booking.created_at.desc()).all()
    return render_template('customer/dashboard.html', bookings=my_bookings)

# --- Browse Tours ---
@customer_bp.route('/tours')
@login_required
def tours():
    today = date.today()
    published_tours = TourGroup.query.filter(
        TourGroup.status == 'published',
        TourGroup.price_published == True,
        TourGroup.deadline_date >= today,
        TourGroup.current_participants < TourGroup.max_participants
    ).order_by(TourGroup.departure_date).all()
    return render_template('customer/tours.html', tours=published_tours, today=today)

@customer_bp.route('/tours/<int:id>')
@login_required
def tour_detail(id):
    group = TourGroup.query.get_or_404(id)
    return render_template('customer/tour_detail.html', group=group)

# --- Booking ---
@customer_bp.route('/tours/<int:id>/book', methods=['GET', 'POST'])
@login_required
def book_tour(id):
    group = TourGroup.query.get_or_404(id)

    if group.status != 'published':
        flash('该旅游团暂不可预订。', 'warning')
        return redirect(url_for('customer.tours'))

    if date.today() > group.deadline_date:
        flash('该旅游团已过截止日期。', 'warning')
        return redirect(url_for('customer.tours'))

    if group.current_participants >= group.max_participants:
        flash('该旅游团已满员。', 'warning')
        return redirect(url_for('customer.tours'))

    if request.method == 'GET':
        days_to_departure = (group.departure_date - date.today()).days
        return render_template('customer/book_tour.html', group=group, days_to_departure=days_to_departure)

    if request.method == 'POST':
        applicant_name = request.form['applicant_name']
        applicant_phone = request.form['applicant_phone']
        adult_count = int(request.form['adult_count'])
        child_count = int(request.form['child_count'])

        total_participants = adult_count + child_count
        if group.current_participants + total_participants > group.max_participants:
            flash('报名人数超过剩余名额。', 'danger')
            days_to_departure = (group.departure_date - date.today()).days
            return render_template('customer/book_tour.html', group=group, days_to_departure=days_to_departure)

        # Calculate deposit based on days before departure
        days_to_departure = (group.departure_date - date.today()).days
        if days_to_departure >= 30:
            deposit_per_person = (group.adult_price * 0.2) if days_to_departure >= 60 else (group.adult_price * 0.3)
        elif days_to_departure >= 20:
            deposit_per_person = group.adult_price * 0.4
        elif days_to_departure >= 10:
            deposit_per_person = group.adult_price * 0.5
        elif days_to_departure >= 2:
            deposit_per_person = group.adult_price * 0.8
        else:
            deposit_per_person = group.adult_price

        adult_deposit = deposit_per_person * adult_count
        child_deposit = (deposit_per_person * 0.6) * child_count
        total_deposit = adult_deposit + child_deposit
        total_amount = group.adult_price * adult_count + group.child_price * child_count
        balance_amount = total_amount - total_deposit

        # Generate booking number
        booking_no = f'BK{date.today().strftime("%Y%m%d")}{Booking.query.count() + 1:04d}'

        booking = Booking(
            booking_no=booking_no,
            tour_group_id=id,
            applicant_name=applicant_name,
            applicant_phone=applicant_phone,
            adult_count=adult_count,
            child_count=child_count,
            deposit_amount=total_deposit,
            total_amount=total_amount,
            balance_amount=balance_amount,
            customer_id=current_user.id,
            created_by=current_user.id
        )
        db.session.add(booking)
        db.session.commit()

        flash(f'预订申请已提交，订金: ¥{total_deposit:.2f}。请尽快前往旅行社支付订金。', 'success')
        return redirect(url_for('customer.my_bookings'))

    return render_template('customer/book_tour.html', group=group)

# --- My Bookings ---
@customer_bp.route('/bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(customer_id=current_user.id) \
                     .order_by(Booking.created_at.desc()).all()
    return render_template('customer/my_bookings.html', bookings=bookings)

@customer_bp.route('/bookings/<int:id>')
@login_required
def booking_detail(id):
    booking = Booking.query.get_or_404(id)
    if booking.customer_id != current_user.id:
        flash('无权查看此预订。', 'danger')
        return redirect(url_for('customer.my_bookings'))
    participants = Participant.query.filter_by(booking_id=id).all()
    payments = Payment.query.filter_by(booking_id=id).order_by(Payment.paid_at.desc()).all()
    cancellations = Cancellation.query.filter_by(booking_id=id).all()
    return render_template('customer/booking_detail.html', booking=booking,
                           participants=participants, payments=payments,
                           cancellations=cancellations)

@customer_bp.route('/bookings/<int:id>/request-cancel', methods=['POST'])
@login_required
def request_cancel(id):
    booking = Booking.query.get_or_404(id)
    if booking.customer_id != current_user.id:
        flash('无权操作。', 'danger')
        return redirect(url_for('customer.my_bookings'))
    if booking.status == 'cancelled':
        flash('该预订已取消。', 'warning')
        return redirect(url_for('customer.booking_detail', id=id))

    booking.status = 'pending_cancel'
    db.session.commit()
    flash('取消请求已提交，请前往旅行社办理取消手续。', 'info')
    return redirect(url_for('customer.booking_detail', id=id))

# --- Profile ---
@customer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.phone = request.form.get('phone', '')
        current_user.email = request.form.get('email', '')
        if request.form.get('new_password'):
            if current_user.check_password(request.form['current_password']):
                current_user.set_password(request.form['new_password'])
                flash('密码已更新。', 'success')
            else:
                flash('当前密码错误。', 'danger')
                return render_template('customer/profile.html')
        db.session.commit()
        flash('个人信息已更新。', 'success')
        return redirect(url_for('customer.profile'))
    return render_template('customer/profile.html')
