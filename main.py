from flask import Flask, request, redirect, url_for, render_template_string, session
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'supersecretkey'

USERNAME = 'admin'
PASSWORD = 'Password@123'

# --- CLOUDINARY CONFIGURATION ---
cloudinary.config(
    cloud_name='dvygrx12d',
    api_key='234675925782836',
    api_secret='jZOlVFcZkz5QhcXcXvia6yGqaDo',
    secure=True
)

# In-memory list to store uploads (use a DB for production persistence)
entries = []

# -------------------- AUTH DECORATOR --------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- LANDING PAGE --------------------
landing_html = '''
<!doctype html>
<html>
<head>
  <title>Upload Portal</title>
  <style>
    body { font-family: Arial; background: #121212; color: white; text-align: center; padding: 50px; }
    form { background: #1f1f1f; padding: 20px; border-radius: 10px; display: inline-block; }
    input, textarea { width: 300px; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
    button { padding: 10px 20px; border: none; background: #03dac6; color: #000; border-radius: 5px; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Upload a File or Text</h1>
  <form method="POST" enctype="multipart/form-data">
    <input type="file" name="file"><br>
    <textarea name="text" placeholder="Or enter some text"></textarea><br>
    <button type="submit">Upload</button>
  </form>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # File Upload
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            upload_result = cloudinary.uploader.upload(file, resource_type="auto")
            entries.append({
                'name': file.filename,
                'url': upload_result['secure_url'],
                'timestamp': timestamp,
                'is_text': False
            })

        # Text Upload
        elif 'text' in request.form and request.form['text'].strip() != '':
            text_content = request.form['text']
            filename = datetime.now().strftime('%Y%m%d%H%M%S_text.txt')
            with open(filename, 'w') as f:
                f.write(text_content)
            upload_result = cloudinary.uploader.upload(filename, resource_type="raw")
            os.remove(filename)
            entries.append({
                'name': filename,
                'url': upload_result['secure_url'],
                'timestamp': timestamp,
                'is_text': True,
                'text': text_content
            })

        return redirect(url_for('index'))

    return render_template_string(landing_html)

# -------------------- LOGIN --------------------
login_html = '''
<!doctype html>
<html>
<head>
  <title>Login</title>
  <style>
    body { font-family: Arial; background: #121212; color: white; text-align: center; padding: 50px; }
    form { background: #1f1f1f; padding: 20px; border-radius: 10px; display: inline-block; }
    input { width: 250px; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
    button { padding: 10px 20px; border: none; background: #03dac6; color: #000; border-radius: 5px; cursor: pointer; }
    p { color: red; }
  </style>
</head>
<body>
  <h1>Login to View Results</h1>
  <form method="POST">
    <input type="text" name="username" placeholder="Username"><br>
    <input type="password" name="password" placeholder="Password"><br>
    <button type="submit">Login</button>
    {% if error %}<p>{{ error }}</p>{% endif %}
  </form>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('results'))
        else:
            error = 'Invalid Credentials'
    return render_template_string(login_html, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# -------------------- RESULTS --------------------
results_html = '''
<!doctype html>
<html>
<head>
  <title>Results</title>
  <style>
    body { font-family: Arial; background: #121212; color: white; padding: 40px; position: relative; }
    .card { background: #1f1f1f; padding: 20px; margin: 10px 0; border-radius: 10px; }
    a { color: #03dac6; margin-right: 10px; }
    .text-preview { background: #333; padding: 10px; border-radius: 5px; white-space: pre-wrap; }
    .timestamp { font-size: 0.9em; color: #bbb; }
    .logout { position: absolute; top: 20px; right: 40px; }
    .logout a { color: #ff6b6b; text-decoration: none; font-weight: bold; }
  </style>
</head>
<body>
  <div class="logout"><a href="/logout">Logout</a></div>
  <h1>Uploaded Files and Texts</h1>
  {% for entry in entries %}
    <div class="card">
      <strong>{{ entry.name }}</strong><br>
      <div class="timestamp">Uploaded: {{ entry.timestamp }}</div>
      {% if entry.is_text %}
        <div class="text-preview">{{ entry.text }}</div><br>
      {% endif %}
      <a href="{{ entry.url }}" target="_blank">View/Download</a>
    </div>
  {% endfor %}
</body>
</html>
'''

@app.route('/results')
@login_required
def results():
    return render_template_string(results_html, entries=entries)

# No `app.run()` here — Gunicorn will handle it in production
