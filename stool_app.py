import os
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from flask_htmx import HTMX
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
from utils import get_timezone

load_dotenv()

app = Flask(__name__)
htmx = HTMX(app)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    SQLALCHEMY_DATABASE_URI='sqlite:///poop_tracker.db',
)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore


def now_tz():
    tz = get_timezone()
    return datetime.now(tz)


@app.template_filter('localtime')
def localtime_filter(dt):
    if not isinstance(dt, datetime):
        return ''
    local_tz = get_timezone()
    # Ensure dt has timezone info before conversion
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    local_dt = dt.astimezone(local_tz)
    return local_dt.strftime('%Y-%m-%d %I:%M %p')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(80))
    family_members = db.relationship(
        'FamilyMember',
        backref='parent',
        lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    records = db.relationship(
        'PoopRecord',
        backref='family_member',
        lazy=True,
        order_by='PoopRecord.timestamp.desc()'
    )


class PoopRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: now_tz())
    poop_type = db.Column(db.String(50))
    family_member_id = db.Column(
        db.Integer,
        db.ForeignKey('family_member.id'),
        nullable=False
    )

    @property
    def timestamp_tz(self):
        """Return timezone-aware timestamp"""
        if self.timestamp.tzinfo is None:
            return pytz.UTC.localize(self.timestamp)
        return self.timestamp


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    print("Register route accessed")  # Debug log
    if request.method == 'POST':
        print("POST request received")  # Debug log
        print("Form data:", request.form)  # Debug log
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User()
        user.email = email
        user.name = name
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("User registered successfully")  # Debug log

        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Login attempt for email: {email}")  # Debug log

        user = User.query.filter_by(email=email).first()
        print(f"User found: {user is not None}")  # Debug log

        if user and user.check_password(password):
            print("Password check passed")  # Debug log
            login_user(user)
            return redirect(url_for('dashboard'))

        print("Login failed")  # Debug log
        flash('Invalid email or password')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    family_members = current_user.family_members
    now = now_tz()
    return render_template(
        'dashboard.html',
        family_members=family_members,
        now=now
    )

@app.route('/member-records/<int:member_id>')
@login_required
def get_member_records(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    if member.parent != current_user:
        return "Access denied", 403

    now = now_tz()  # This is already timezone-aware

    # Handle date range filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = PoopRecord.query.filter_by(family_member_id=member.id)
    
    if not start_date and not end_date:
        seven_days_ago = now - timedelta(days=7)
        query = query.filter(PoopRecord.timestamp >= seven_days_ago)
    else:
        local_tz = get_timezone()
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            start_dt = local_tz.localize(start_dt)
            query = query.filter(PoopRecord.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Set time to end of day for the end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            end_dt = local_tz.localize(end_dt)
            query = query.filter(PoopRecord.timestamp <= end_dt)

    member.records = query.order_by(PoopRecord.timestamp.desc()).all()

    return render_template(
        'partials/member_records.html',
        member=member,
        now=now
    )


@app.route('/delete-record/<int:record_id>', methods=['DELETE'])
@login_required
def delete_record(record_id):
    record = PoopRecord.query.get_or_404(record_id)
    if record.family_member.parent != current_user:
        return "Access denied", 403

    db.session.delete(record)
    db.session.commit()
    return '', 200


@app.route('/remove-family-member/<int:member_id>', methods=['DELETE'])
@login_required
def remove_family_member(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    if member.parent != current_user:
        return "Access denied", 403

    # Delete all associated records first
    PoopRecord.query.filter_by(family_member_id=member.id).delete()

    # Then delete the family member
    db.session.delete(member)
    db.session.commit()

    # Return status 200
    return '', 200


@app.route('/add_family_member', methods=['GET', 'POST'])
@login_required
def add_family_member():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            member = FamilyMember(name=name, parent=current_user)
            db.session.add(member)
            db.session.commit()
            flash(f'Added family member: {name}')
            return redirect(url_for('dashboard'))
        flash('Name is required')
    return render_template('add_family_member.html')


@app.route('/record/<int:member_id>', methods=['GET', 'POST'])
@login_required
def record(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    if member.parent != current_user:
        flash('Access denied')
        return redirect(url_for('dashboard'))

    local_tz = get_timezone()
    now = now_tz()

    if request.method == 'POST':
        poop_type = request.form.get('poop_type')
        date_str = request.form.get('date')
        time_str = request.form.get('time')

        if poop_type and date_str and time_str:
            try:
                timestamp_str = f"{date_str} {time_str}"
                # timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                # timestamp = local_tz.localize(timestamp).astimezone(pytz.UTC)
                naive_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                # Localize the naive datetime to the local timezone
                local_timestamp = local_tz.localize(naive_timestamp)
                # Convert local time to UTC
                utc_timestamp = local_timestamp.astimezone(pytz.UTC)
                record = PoopRecord(
                    poop_type=poop_type,
                    family_member=member,
                    timestamp=utc_timestamp,
                )
                db.session.add(record)
                db.session.commit()
                print(f"now: {timestamp_str}")
                print(f"Naive timestamp: {naive_timestamp}")
                print(f"Local timestamp: {local_timestamp}")
                print(f"UTC timestamp: {utc_timestamp}")

                flash('Record added successfully')
                return redirect(url_for('dashboard'))
            except ValueError:
                flash('Invalid date or time format')
                return render_template('record.html', member=member, now=now)
        flash('Please select a poop type, date and time')
    return render_template('record.html', member=member, now=now)


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database created successfully!")
        except Exception as e:
            print(f"Error creating database: {e}")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
