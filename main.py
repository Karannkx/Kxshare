import os
import base64
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file, abort
from tinydb import TinyDB, Query
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests
from dotenv import load_dotenv
import markdown
import io
import zipfile

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Set this in .env file

# Initialize TinyDB
db = TinyDB('database.json')

# Generate encryption key from SECRET_KEY
def get_encryption_key():
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'salt_',  # In production, use a random salt per user
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return Fernet(key)

cipher = get_encryption_key()

# Homepage route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        token = request.form['token']
        repo_url = request.form['repo_url']
        expiry_days = int(request.form['expiry_days'])

        # Encrypt token
        encrypted_token = cipher.encrypt(token.encode())

        # Extract owner and repo from URL
        try:
            repo_path = repo_url.split('github.com/')[1].rstrip('/')
            owner, repo = repo_path.split('/')
        except:
            return "Invalid GitHub URL", 400

        # Generate unique share ID
        share_id = str(uuid.uuid4())

        # Store in database
        db.insert({
            'share_id': share_id,
            'encrypted_token': encrypted_token.decode(),
            'owner': owner,
            'repo': repo,
            'created_at': datetime.now().isoformat(),
            'expiry': (datetime.now() + timedelta(days=expiry_days)).isoformat()
        })

        share_link = url_for('view_repo', share_id=share_id, _external=True)
        return render_template('success.html', share_link=share_link)

    return render_template('home.html')

# View repository route
@app.route('/view/<share_id>')
def view_repo(share_id):
    q = Query()
    repo_data = db.search(q.share_id == share_id)

    if not repo_data:
        abort(404)

    repo_data = repo_data[0]
    expiry = datetime.fromisoformat(repo_data['expiry'])

    if datetime.now() > expiry:
        return render_template('expired.html')

    # Decrypt token
    token = cipher.decrypt(repo_data['encrypted_token'].encode()).decode()
    owner = repo_data['owner']
    repo = repo_data['repo']

    # GitHub API headers
    headers = {'Authorization': f'token {token}'}

    # Fetch README
    readme_url = f'https://api.github.com/repos/{owner}/{repo}/readme'
    readme_resp = requests.get(readme_url, headers=headers)

    readme_content = ""
    if readme_resp.status_code == 200:
        readme_text = base64.b64decode(readme_resp.json()['content']).decode('utf-8')
        readme_content = markdown.markdown(readme_text)

    # Fetch repo contents
    contents_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
    contents_resp = requests.get(contents_url, headers=headers)

    files = []
    if contents_resp.status_code == 200:
        files = contents_resp.json()

    return render_template('view.html', 
                         readme_content=readme_content,
                         files=files,
                         owner=owner,
                         repo=repo,
                         share_id=share_id)

# Download ZIP route
@app.route('/download/<share_id>')
def download_repo(share_id):
    q = Query()
    repo_data = db.search(q.share_id == share_id)

    if not repo_data or datetime.now() > datetime.fromisoformat(repo_data[0]['expiry']):
        abort(404)

    repo_data = repo_data[0]
    token = cipher.decrypt(repo_data['encrypted_token'].encode()).decode()
    owner = repo_data['owner']
    repo = repo_data['repo']

    headers = {'Authorization': f'token {token}'}
    zip_url = f'https://api.github.com/repos/{owner}/{repo}/zipball'
    zip_resp = requests.get(zip_url, headers=headers, stream=True)

    if zip_resp.status_code != 200:
        abort(404)

    # Create in-memory ZIP file
    zip_buffer = io.BytesIO(zip_resp.content)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{repo}.zip'
    )

# HTML Templates as strings (in production, these would be in separate files)
home_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Share GitHub Repo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        input, select, button { margin: 10px 0; padding: 5px; }
    </style>
</head>
<body>
    <h1>Share Private GitHub Repository</h1>
    <form method="POST">
        <input type="text" name="token" placeholder="GitHub Personal Access Token" required><br>
        <input type="text" name="repo_url" placeholder="Repository URL (e.g., https://github.com/owner/repo)" required><br>
        <select name="expiry_days">
            <option value="1">1 Day</option>
            <option value="7">7 Days</option>
            <option value="30">30 Days</option>
        </select><br>
        <button type="submit">Generate Share Link</button>
    </form>
</body>
</html>
'''

success_template = '''
<!DOCTYPE html>
<html>
<head><title>Link Generated</title></head>
<body>
    <h1>Share Link Generated</h1>
    <p>Your share link: <a href="{{ share_link }}">{{ share_link }}</a></p>
    <p>Copy this link and share it with others. It will expire as per your selected time.</p>
</body>
</html>
'''

view_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ owner }}/{{ repo }}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .file-list { list-style: none; padding: 0; }
        .file-list li { margin: 5px 0; }
    </style>
</head>
<body>
    <h1>{{ owner }}/{{ repo }}</h1>
    <h2>README</h2>
    <div>{{ readme_content | safe }}</div>
    <h2>Files</h2>
    <ul class="file-list">
        {% for file in files %}
            <li>{{ file.name }} ({{ file.type }})</li>
        {% endfor %}
    </ul>
    <a href="{{ url_for('download_repo', share_id=share_id) }}">Download ZIP</a>
</body>
</html>
'''

expired_template = '''
<!DOCTYPE html>
<html>
<head><title>Expired</title></head>
<body>
    <h1>Link Expired</h1>
    <p>This share link has expired.</p>
</body>
</html>
'''

# Register templates
app.jinja_env.globals.update({
    'home.html': home_template,
    'success.html': success_template,
    'view.html': view_template,
    'expired.html': expired_template
})

if __name__ == '__main__':
    app.run(debug=True)