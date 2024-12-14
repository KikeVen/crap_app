from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os
import pytz  # You may need to install this: pip install pytz


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poop_tracker.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # type: ignore


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
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    poop_type = db.Column(db.String(50))
    family_member_id = db.Column(
        db.Integer,
        db.ForeignKey('family_member.id'),
        nullable=False
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))

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
    now = datetime.now(timezone.utc)
    return render_template(
        'dashboard.html',
        family_members=family_members,
        now=now
    )


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
    
    # Get your local timezone - replace 'America/New_York' with your timezone
    local_tz = pytz.timezone('America/Caracas')  # America/New_York
    
    # Convert UTC time to local time
    now = datetime.now(pytz.UTC).astimezone(local_tz)
    
    if request.method == 'POST':
        poop_type = request.form.get('poop_type')
        date_str = request.form.get('date')
        time_str = request.form.get('time')

        if poop_type and date_str and time_str:
            try:
                timestamp_str = f"{date_str} {time_str}"
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                record = PoopRecord(
                    poop_type=poop_type,
                    family_member=member,
                    timestamp=timestamp
                )
                db.session.add(record)
                db.session.commit()
                flash('Record added successfully')
                return redirect(url_for('dashboard'))
            except ValueError:
                flash('Invalid date or time format')
                return render_template('record.html', member=member, now=now)
        flash('Please select a poop type, date and time')
    return render_template('record.html', member=member, now=now)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
