from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'yourmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'yourpassword'
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# Create upload folder if not exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- HELPERS ----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- HOME ----------------
@app.route('/')
def home():
    videos = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', videos=videos)

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))

    return render_template('login.html')

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/login')

    videos = os.listdir(UPLOAD_FOLDER)
    return render_template('admin.html', videos=videos)

# ---------------- DELETE ----------------
@app.route('/delete/<filename>')
def delete(filename):
    if not session.get('admin'):
        return redirect('/login')

    os.remove(os.path.join(UPLOAD_FOLDER, filename))
    return redirect('/admin')

# ---------------- UPLOAD ----------------
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('video')

    if file and allowed_file(file.filename):
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        return redirect('/')
    
    return "Only video files allowed!"

# ---------------- CONTACT (MAIL) ----------------
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    message = request.form.get('message')

    msg = Message(
        "New Client Message",
        sender=app.config['MAIL_USERNAME'],
        recipients=[app.config['MAIL_USERNAME']]
    )

    msg.body = f"Name: {name}\nMessage: {message}"
    mail.send(msg)

    return redirect('/')

# ---------------- SERVE VIDEOS ----------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)