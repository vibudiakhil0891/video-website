from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    videos = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['video']

    if file and allowed_file(file.filename):
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return redirect(url_for('home'))
    else:
        return "Only video files allowed!"

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    message = request.form['message']

    print(f"{name}: {message}")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

    from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
    file = request.files['video']
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return redirect('/')

# ---------------- CONTACT ----------------
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    message = request.form['message']

    print(f"{name}: {message}")
    return redirect('/')

# ---------------- SERVE VIDEOS ----------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)

from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'yourmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'yourpassword'
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    message = request.form['message']

    msg = Message("New Client Message",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=['yourmail@gmail.com'])

    msg.body = f"Name: {name}\nMessage: {message}"
    mail.send(msg)

    return redirect('/')