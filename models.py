from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # admin, staff, customer
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff(self):
        return self.role in ('admin', 'staff')

class TourRoute(db.Model):
    __tablename__ = 'tour_routes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    destination = db.Column(db.String(200))
    duration_days = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    creator = db.relationship('User', backref='routes')
    history = db.relationship('RouteHistory', backref='route', lazy='dynamic',
                              order_by='RouteHistory.changed_at.desc()')

class RouteHistory(db.Model):
    __tablename__ = 'route_history'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('tour_routes.id'), nullable=False)
    field_name = db.Column(db.String(100))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    changer = db.relationship('User')

class TourGroup(db.Model):
    __tablename__ = 'tour_groups'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('tour_routes.id'), nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    deadline_date = db.Column(db.Date, nullable=False)
    max_participants = db.Column(db.Integer, default=30)
    current_participants = db.Column(db.Integer, default=0)
    adult_price = db.Column(db.Float, default=0)
    child_price = db.Column(db.Float, default=0)
    discount_info = db.Column(db.Text)
    price_published = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='draft')  # draft, published, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    route = db.relationship('TourRoute', backref='tour_groups')
    creator = db.relationship('User', backref='tour_groups')
    price_history = db.relationship('PriceHistory', backref='tour_group', lazy='dynamic',
                                    order_by='PriceHistory.changed_at.desc()')

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    id = db.Column(db.Integer, primary_key=True)
    tour_group_id = db.Column(db.Integer, db.ForeignKey('tour_groups.id'), nullable=False)
    adult_price = db.Column(db.Float)
    child_price = db.Column(db.Float)
    discount_info = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    changer = db.relationship('User')

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    booking_no = db.Column(db.String(30), unique=True, nullable=False)
    tour_group_id = db.Column(db.Integer, db.ForeignKey('tour_groups.id'), nullable=False)
    applicant_name = db.Column(db.String(100), nullable=False)
    applicant_phone = db.Column(db.String(20), nullable=False)
    adult_count = db.Column(db.Integer, default=0)
    child_count = db.Column(db.Integer, default=0)
    deposit_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    deposit_paid = db.Column(db.Boolean, default=False)
    deposit_paid_at = db.Column(db.DateTime)
    balance_amount = db.Column(db.Float, default=0)
    balance_paid = db.Column(db.Boolean, default=False)
    balance_paid_at = db.Column(db.DateTime)
    payment_deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    participants_entered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    tour_group = db.relationship('TourGroup', backref='bookings')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_bookings')
    customer = db.relationship('User', foreign_keys=[customer_id], backref='customer_bookings')
    participants = db.relationship('Participant', backref='booking', lazy='dynamic')
    payments = db.relationship('Payment', backref='booking', lazy='dynamic',
                               order_by='Payment.paid_at.desc()')

class Participant(db.Model):
    __tablename__ = 'participants'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    participant_type = db.Column(db.String(10), default='adult')  # adult, child
    is_applicant = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')  # active, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # deposit, balance, refund
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    exported = db.Column(db.Boolean, default=False)

    recorder = db.relationship('User')

class Cancellation(db.Model):
    __tablename__ = 'cancellations'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=True)
    cancel_type = db.Column(db.String(20), nullable=False)  # participant, entire
    cancellation_fee = db.Column(db.Float, default=0)
    refund_amount = db.Column(db.Float, default=0)
    new_applicant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    booking = db.relationship('Booking', backref='cancellations')
    participant = db.relationship('Participant', foreign_keys=[participant_id])
    new_applicant = db.relationship('Participant', foreign_keys=[new_applicant_id])
    canceller = db.relationship('User')
