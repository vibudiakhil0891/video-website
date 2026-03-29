# ================= IMPORTS =================
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, uuid
import razorpay

# ================= INIT =================
app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# MAIL CONFIG
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'yourmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'
app.config['MAIL_USE_TLS'] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Razorpay
RAZORPAY_KEY_ID = "your_key_id"
RAZORPAY_KEY_SECRET = "your_secret"
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ADMIN
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ================= MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))

    videos = db.relationship('Video', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    description = db.Column(db.Text)
    price = db.Column(db.Integer, default=500)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ================= HELPERS =================
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================= ROUTES =================

# ---------- HOME ----------
@app.route('/')
def home():
    if not session.get('user_id'):
        videos = []
        orders = []
    else:
        videos = Video.query.filter_by(
            user_id=session['user_id'],
            status="approved"
        ).all()
        orders = Order.query.filter_by(
            user_id=session['user_id']
        ).all()

    return render_template('index.html', videos=videos, orders=orders)

# ---------- USER AUTH ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        existing = User.query.filter_by(email=request.form['email']).first()
        if existing:
            return render_template('signup.html', error="Email already exists!")

        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/user-login')

    return render_template('signup.html')

@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect('/')
        return render_template('user_login.html', error="Invalid login")
    return render_template('user_login.html')

@app.route('/user-logout')
def user_logout():
    session.pop('user_id', None)
    return redirect('/')

# ---------- ADMIN AUTH ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

# ---------- ADMIN DASHBOARD ----------
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/login')

    videos = Video.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()

    analytics = {
        "total_videos": Video.query.count(),
        "pending_videos": Video.query.filter_by(status='pending').count(),
        "total_orders": Order.query.count(),
        "total_revenue": db.session.query(db.func.sum(Order.price)).filter_by(status='paid').scalar() or 0
    }

    return render_template('admin.html', videos=videos, orders=orders, analytics=analytics)

# ---------- VIDEO UPLOAD ----------
@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('user_id'):
        return redirect('/user-login')

    file = request.files.get('video')
    if file and allowed_file(file.filename):
        name = str(uuid.uuid4()) + "_" + file.filename
        file.save(os.path.join(UPLOAD_FOLDER, name))

        video = Video(
            filename=name,
            category=request.form.get('category'),
            user_id=session['user_id']
        )
        db.session.add(video)
        db.session.commit()

    return redirect('/')

@app.route('/status/<int:video_id>/<new_status>')
def update_status(video_id, new_status):
    if not session.get('admin'):
        return redirect('/login')
    video = Video.query.get_or_404(video_id)
    video.status = new_status
    db.session.commit()
    return redirect('/admin')

# ---------- ORDERS ----------
@app.route('/create-order', methods=['POST'])
def create_order():
    if not session.get('user_id'):
        return redirect('/user-login')

    order = Order(
        user_id=session['user_id'],
        video_id=request.form['video_id'],
        description=request.form['description']
    )
    db.session.add(order)
    db.session.commit()
    return redirect('/')

# ---------- PAYMENTS ----------
@app.route('/pay/<int:order_id>')
def pay(order_id):
    if not session.get('user_id'):
        return redirect('/user-login')

    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        return "Unauthorized"

    razorpay_order = client.order.create({
        "amount": order.price * 100,
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template('pay.html',
                           order=order,
                           razorpay_order=razorpay_order,
                           key_id=RAZORPAY_KEY_ID)

@app.route('/payment-success/<int:order_id>')
def payment_success(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = "paid"
    db.session.commit()
    return redirect('/')

@app.route('/my-orders')
def my_orders():
    if not session.get('user_id'):
        return redirect('/user-login')

    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

# ---------- CONTACT ----------
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    msg = Message(subject=f"New message from {name}",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[app.config['MAIL_USERNAME']],
                  body=f"From: {name} <{email}>\n\n{message}")
    mail.send(msg)
    return "OK"

# ---------- RUN ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# ================= USER SIGNUP =================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate inputs
        if not username or not email or not password:
            return render_template('signup.html', error="All fields are required!")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('signup.html', error="Email already exists!")

        # Create user
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        return redirect('/user-login')

    # GET request
    return render_template('signup.html')


# ================= USER LOGIN =================
@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form.get('username')  # matches input name in login.html
        password = request.form.get('password')

        # Validate inputs
        if not email or not password:
            return render_template('user_login.html', error="Please enter both email and password")

        # Check user
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/')
        else:
            return render_template('user_login.html', error="Invalid email or password")

    # GET request
    return render_template('user_login.html')


# ================= USER LOGOUT =================
@app.route('/user-logout')
def user_logout():
    session.pop('user_id', None)
    return redirect('/')