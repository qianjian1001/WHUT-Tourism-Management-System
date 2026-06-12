from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, TourRoute, TourGroup, Booking, Participant, Payment, Cancellation, PriceHistory, RouteHistory, User
from datetime import datetime, date, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def staff_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            flash('需要员工权限。', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/')
@login_required
@staff_required
def dashboard():
    total_routes = TourRoute.query.filter_by(status='active').count()
    total_groups = TourGroup.query.filter(TourGroup.status.in_(['published', 'draft'])).count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending', deposit_paid=True).count()
    today = date.today()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    expiring_payments = Booking.query.filter(
        Booking.balance_paid == False,
        Booking.deposit_paid == True,
        Booking.status == 'confirmed',
        Booking.payment_deadline <= today + timedelta(days=7)
    ).all()

    return render_template('admin/dashboard.html',
                           total_routes=total_routes,
                           total_groups=total_groups,
                           total_bookings=total_bookings,
                           pending_bookings=pending_bookings,
                           recent_bookings=recent_bookings,
                           expiring_payments=expiring_payments)

# --- Tour Route Management ---
@admin_bp.route('/routes')
@login_required
@staff_required
def routes():
    routes_list = TourRoute.query.order_by(TourRoute.created_at.desc()).all()
    return render_template('admin/routes.html', routes=routes_list, User=User)

@admin_bp.route('/routes/add', methods=['POST'])
@login_required
@staff_required
def add_route():
    code = request.form['code']
    name = request.form['name']
    destination = request.form.get('destination', '')
    description = request.form.get('description', '')
    duration_days = int(request.form.get('duration_days', 1))

    existing = TourRoute.query.filter_by(code=code).first()
    if existing:
        flash('路线代码已存在。', 'danger')
        return redirect(url_for('admin.routes'))

    route = TourRoute(code=code, name=name, destination=destination,
                      description=description, duration_days=duration_days,
                      created_by=current_user.id)
    db.session.add(route)
    db.session.commit()
    flash('路线添加成功。', 'success')
    return redirect(url_for('admin.routes'))

@admin_bp.route('/routes/<int:id>/edit', methods=['POST'])
@login_required
@staff_required
def edit_route(id):
    route = TourRoute.query.get_or_404(id)
    old_name = route.name
    old_dest = route.destination
    old_desc = route.description
    old_dur = route.duration_days

    route.name = request.form['name']
    route.destination = request.form.get('destination', '')
    route.description = request.form.get('description', '')
    route.duration_days = int(request.form.get('duration_days', 1))

    # Record history
    if old_name != route.name:
        db.session.add(RouteHistory(route_id=id, field_name='name', old_value=old_name,
                                    new_value=route.name, changed_by=current_user.id))
    if old_dest != route.destination:
        db.session.add(RouteHistory(route_id=id, field_name='destination', old_value=old_dest or '',
                                    new_value=route.destination, changed_by=current_user.id))
    if old_desc != route.description:
        db.session.add(RouteHistory(route_id=id, field_name='description', old_value=old_desc or '',
                                    new_value=route.description, changed_by=current_user.id))
    if old_dur != route.duration_days:
        db.session.add(RouteHistory(route_id=id, field_name='duration_days', old_value=str(old_dur),
                                    new_value=str(route.duration_days), changed_by=current_user.id))

    db.session.commit()
    flash('路线更新成功，变更历史已记录。', 'success')
    return redirect(url_for('admin.routes'))

@admin_bp.route('/routes/<int:id>/toggle')
@login_required
@staff_required
def toggle_route(id):
    route = TourRoute.query.get_or_404(id)
    route.status = 'inactive' if route.status == 'active' else 'active'
    db.session.commit()
    flash(f'路线状态已更新为{"启用" if route.status == "active" else "停用"}。', 'info')
    return redirect(url_for('admin.routes'))

@admin_bp.route('/routes/<int:id>/history')
@login_required
@staff_required
def route_history(id):
    route = TourRoute.query.get_or_404(id)
    history = RouteHistory.query.filter_by(route_id=id).order_by(RouteHistory.changed_at.desc()).all()
    return render_template('admin/route_history.html', route=route, history=history, User=User)

# --- Tour Group Management ---
@admin_bp.route('/tour-groups')
@login_required
@staff_required
def tour_groups():
    groups = TourGroup.query.order_by(TourGroup.departure_date.desc()).all()
    routes = TourRoute.query.filter_by(status='active').all()
    return render_template('admin/tour_groups.html', groups=groups, routes=routes, User=User)

@admin_bp.route('/tour-groups/add', methods=['POST'])
@login_required
@staff_required
def add_tour_group():
    code = request.form['code']
    route_id = int(request.form['route_id'])
    departure_date = datetime.strptime(request.form['departure_date'], '%Y-%m-%d').date()
    return_date_str = request.form.get('return_date', '')
    return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date() if return_date_str else None
    deadline_date = datetime.strptime(request.form['deadline_date'], '%Y-%m-%d').date()
    max_participants = int(request.form['max_participants'])

    existing = TourGroup.query.filter_by(code=code).first()
    if existing:
        flash('团号已存在。', 'danger')
        return redirect(url_for('admin.tour_groups'))

    group = TourGroup(code=code, route_id=route_id, departure_date=departure_date,
                      return_date=return_date, deadline_date=deadline_date,
                      max_participants=max_participants, created_by=current_user.id)
    db.session.add(group)
    db.session.commit()
    flash('旅游团添加成功。', 'success')
    return redirect(url_for('admin.tour_groups'))

@admin_bp.route('/tour-groups/<int:id>/pricing', methods=['POST'])
@login_required
@staff_required
def set_pricing(id):
    group = TourGroup.query.get_or_404(id)
    adult_price = float(request.form['adult_price'])
    child_price = float(request.form.get('child_price', 0))
    discount_info = request.form.get('discount_info', '')

    # Record price history
    db.session.add(PriceHistory(
        tour_group_id=id,
        adult_price=group.adult_price,
        child_price=group.child_price,
        discount_info=group.discount_info,
        changed_by=current_user.id
    ))

    group.adult_price = adult_price
    group.child_price = child_price
    group.discount_info = discount_info
    db.session.commit()
    flash('价格设定成功。', 'success')
    return redirect(url_for('admin.tour_groups'))

@admin_bp.route('/tour-groups/<int:id>/publish-price')
@login_required
@staff_required
def publish_price(id):
    group = TourGroup.query.get_or_404(id)
    if group.adult_price <= 0:
        flash('请先设定有效的价格后再发布。', 'danger')
        return redirect(url_for('admin.tour_groups'))
    group.price_published = True
    group.status = 'published'
    db.session.commit()
    flash('价格已发布，该旅游团已对客户公开。', 'success')
    return redirect(url_for('admin.tour_groups'))

@admin_bp.route('/tour-groups/<int:id>/toggle-status')
@login_required
@staff_required
def toggle_group_status(id):
    group = TourGroup.query.get_or_404(id)
    if group.status == 'published':
        group.status = 'cancelled'
    elif group.status == 'draft':
        group.status = 'published' if group.price_published else 'draft'
        if not group.price_published:
            flash('请先发布价格。', 'warning')
            return redirect(url_for('admin.tour_groups'))
    elif group.status == 'cancelled':
        group.status = 'published' if group.price_published else 'draft'
    db.session.commit()
    flash(f'团状态已更新。', 'info')
    return redirect(url_for('admin.tour_groups'))

# --- Booking Management ---
@admin_bp.route('/bookings')
@login_required
@staff_required
def bookings():
    bookings_list = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings_list)

@admin_bp.route('/bookings/<int:id>')
@login_required
@staff_required
def booking_detail(id):
    booking = Booking.query.get_or_404(id)
    participants = Participant.query.filter_by(booking_id=id).all()
    payments = Payment.query.filter_by(booking_id=id).order_by(Payment.paid_at.desc()).all()
    cancellations = Cancellation.query.filter_by(booking_id=id).all()
    return render_template('admin/booking_detail.html', booking=booking,
                           participants=participants, payments=payments,
                           cancellations=cancellations)

@admin_bp.route('/bookings/<int:id>/confirm-deposit', methods=['POST'])
@login_required
@staff_required
def confirm_deposit(id):
    booking = Booking.query.get_or_404(id)
    booking.deposit_paid = True
    booking.deposit_paid_at = datetime.utcnow()
    booking.status = 'confirmed'

    # Calculate payment deadline
    if booking.payment_deadline is None:
        days_to_departure = (booking.tour_group.departure_date - date.today()).days
        balance_deadline = booking.tour_group.departure_date - timedelta(days=30)
        send_date = date.today()
        if (balance_deadline - send_date).days < 10:
            balance_deadline = send_date + timedelta(days=10)
        if balance_deadline < send_date:
            balance_deadline = send_date + timedelta(days=10)
        booking.payment_deadline = balance_deadline

    db.session.add(Payment(booking_id=id, payment_type='deposit',
                           amount=booking.deposit_amount, recorded_by=current_user.id))
    booking.tour_group.current_participants += (booking.adult_count + booking.child_count)
    db.session.commit()
    flash('订金已确认。', 'success')
    return redirect(url_for('admin.booking_detail', id=id))

@admin_bp.route('/bookings/<int:id>/confirm-balance', methods=['POST'])
@login_required
@staff_required
def confirm_balance(id):
    booking = Booking.query.get_or_404(id)
    amount = float(request.form['amount'])
    booking.balance_paid = True
    booking.balance_paid_at = datetime.utcnow()
    booking.status = 'completed'
    db.session.add(Payment(booking_id=id, payment_type='balance',
                           amount=amount, recorded_by=current_user.id))
    db.session.commit()
    flash('余款已确认。', 'success')
    return redirect(url_for('admin.booking_detail', id=id))

@admin_bp.route('/bookings/<int:id>/cancel', methods=['POST'])
@login_required
@staff_required
def cancel_booking(id):
    booking = Booking.query.get_or_404(id)
    group = booking.tour_group

    days_to_departure = (group.departure_date - date.today()).days
    total_paid = sum(p.amount for p in booking.payments if p.payment_type in ('deposit', 'balance'))

    # Calculate cancellation fee based on days before departure
    if days_to_departure >= 30:
        fee_rate = 0
    elif days_to_departure >= 10:
        fee_rate = 0.2
    elif days_to_departure >= 1:
        fee_rate = 0.5
    else:
        fee_rate = 1.0

    cancellation_fee = total_paid * fee_rate
    refund_amount = total_paid - cancellation_fee

    canc = Cancellation(booking_id=id, cancel_type='entire',
                        cancellation_fee=cancellation_fee, refund_amount=refund_amount,
                        cancelled_by=current_user.id)
    db.session.add(canc)

    if refund_amount > 0:
        db.session.add(Payment(booking_id=id, payment_type='refund',
                               amount=refund_amount, recorded_by=current_user.id))

    booking.status = 'cancelled'
    group.current_participants = max(0, group.current_participants -
                                     (booking.adult_count + booking.child_count))
    db.session.commit()
    flash(f'申请已取消，取消手续费: ¥{cancellation_fee:.2f}，退款: ¥{refund_amount:.2f}', 'info')
    return redirect(url_for('admin.booking_detail', id=id))

# --- Participant Management ---
@admin_bp.route('/bookings/<int:id>/participants/add', methods=['POST'])
@login_required
@staff_required
def add_participant(id):
    booking = Booking.query.get_or_404(id)
    name = request.form['name']
    ptype = request.form['participant_type']
    is_applicant = request.form.get('is_applicant') == 'on'

    current_count = Participant.query.filter_by(booking_id=id, status='active').count()
    expected = booking.adult_count + booking.child_count

    participant = Participant(booking_id=id, name=name, participant_type=ptype,
                              is_applicant=is_applicant)
    db.session.add(participant)
    db.session.commit()

    # Check if all participants are entered
    new_count = Participant.query.filter_by(booking_id=id, status='active').count()
    if new_count >= expected:
        booking.participants_entered = True
        db.session.commit()

    flash(f'参加者 {name} 已添加。', 'success')
    return redirect(url_for('admin.booking_detail', id=id))

@admin_bp.route('/bookings/<int:booking_id>/participants/<int:pid>/cancel', methods=['POST'])
@login_required
@staff_required
def cancel_participant(booking_id, pid):
    booking = Booking.query.get_or_404(booking_id)
    participant = Participant.query.get_or_404(pid)
    group = booking.tour_group

    days_to_departure = (group.departure_date - date.today()).days
    if days_to_departure >= 30:
        fee_rate = 0
    elif days_to_departure >= 10:
        fee_rate = 0.2
    elif days_to_departure >= 1:
        fee_rate = 0.5
    else:
        fee_rate = 1.0

    per_person_deposit = booking.deposit_amount / max(1, booking.adult_count + booking.child_count)
    cancellation_fee = per_person_deposit * fee_rate
    refund_amount = per_person_deposit - cancellation_fee

    if participant.is_applicant:
        other_participant = Participant.query.filter(
            Participant.booking_id == booking_id,
            Participant.id != pid,
            Participant.status == 'active'
        ).first()
        if other_participant:
            booking.applicant_name = other_participant.name
            other_participant.is_applicant = True

    participant.status = 'cancelled'
    canc = Cancellation(booking_id=booking_id, participant_id=pid,
                        cancel_type='participant', cancellation_fee=cancellation_fee,
                        refund_amount=refund_amount, cancelled_by=current_user.id)
    db.session.add(canc)

    if participant.participant_type == 'adult':
        booking.adult_count -= 1
    else:
        booking.child_count -= 1
    booking.tour_group.current_participants = max(0, booking.tour_group.current_participants - 1)

    db.session.commit()
    flash(f'参加者 {participant.name} 已取消。', 'info')
    return redirect(url_for('admin.booking_detail', id=booking_id))

# --- Document Generation ---
@admin_bp.route('/documents/today')
@login_required
@staff_required
def daily_documents():
    yesterday = date.today() - timedelta(days=1)
    # Bookings completed yesterday
    completed = Booking.query.filter(
        Booking.status.in_(['confirmed', 'completed']),
        Booking.deposit_paid == True,
        db.func.date(Booking.deposit_paid_at) == yesterday
    ).all()

    return render_template('admin/documents.html', bookings=completed, yesterday=yesterday)

# --- Reports ---
@admin_bp.route('/reports')
@login_required
@staff_required
def reports():
    return render_template('admin/reports.html')

@admin_bp.route('/reports/export')
@login_required
@staff_required
def export_financial():
    today = date.today()
    unexported = Payment.query.filter_by(exported=False).all()
    export_data = []
    total_deposit = 0
    total_balance = 0
    for p in unexported:
        export_data.append({
            'payment_id': p.id,
            'booking_id': p.booking_id,
            'type': p.payment_type,
            'amount': p.amount,
            'paid_at': p.paid_at.strftime('%Y-%m-%d %H:%M') if p.paid_at else ''
        })
        if p.payment_type == 'deposit':
            total_deposit += p.amount
        elif p.payment_type == 'balance':
            total_balance += p.amount
        p.exported = True
    db.session.commit()
    return render_template('admin/reports.html', export_data=export_data,
                           total_deposit=total_deposit, total_balance=total_balance,
                           exported=True)
