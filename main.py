import os
import base64
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, make_response
from flask_caching import Cache
import qrcode
import base64
from io import BytesIO
from tinydb import TinyDB, Query
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests
from dotenv import load_dotenv
import markdown
import io
import zipfile
from flask import send_from_directory

# Initialize Flask app
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Set this in .env file

# Initialize TinyDB
db = TinyDB('database.json')

# Generate encryption key from SECRET_KEY (for both token and password encryption)
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
        protection_password = request.form.get('protection_password', '')

        # Encrypt token
        encrypted_token = cipher.encrypt(token.encode())

        # Encrypt password if provided
        encrypted_password = cipher.encrypt(protection_password.encode()) if protection_password else ''

        # Extract owner and repo from URL
        try:
            repo_path = repo_url.split('github.com/')[1].rstrip('/')
            owner, repo = repo_path.split('/')
        except:
            return "Invalid GitHub URL", 400

        # Generate unique share ID
        share_id = str(uuid.uuid4())

        # Store in database with encrypted password
        db.insert({
            'share_id': share_id,
            'encrypted_token': encrypted_token.decode(),
            'owner': owner,
            'repo': repo,
            'created_at': datetime.now().isoformat(),
            'expiry': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
            'is_protected': bool(protection_password),
            'password': encrypted_password.decode() if encrypted_password else ''  # Encrypted password
        })

        share_link = url_for('view_repo', share_id=share_id, _external=True)

        # Generate QR code
        qr =qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(share_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert QR code to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # Get expiry date
        expiry_date = (datetime.now() + timedelta(days=int(expiry_days))).strftime('%Y-%m-%dT%H:%M:%S')

        return render_template('success.html', 
                             share_link=share_link, 
                             qr_code=qr_code,
                             expiry_date=expiry_date)

    response = make_response(render_template('home.html'))
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response

# View repository route (updated for encrypted passwords)
@app.route('/view/<share_id>', methods=['GET', 'POST'])
def view_repo(share_id):
    q = Query()
    repo_data = db.search(q.share_id == share_id)

    if not repo_data:
        abort(404)

    repo_data = repo_data[0]
    if repo_data.get('is_protected'):
        if request.method == 'POST':
            entered_password = request.form.get('password', '').strip()
            stored_encrypted_password = repo_data.get('password', '')

            try:
                # Decrypt stored password
                stored_password = cipher.decrypt(stored_encrypted_password.encode()).decode()
                print(f"Debug - Entered: '{entered_password}' (len: {len(entered_password)}), Decrypted Stored: '{stored_password}' (len: {len(stored_password)})")

                if entered_password == stored_password:
                    print("Password matched! Redirecting to repo content...")
                    return render_repo_content(repo_data)
                else:
                    print("Password mismatch! Returning to password page...")
                    return render_template('password.html', share_id=share_id, error="Incorrect password")
            except Exception as e:
                print(f"Decryption error: {e}")
                return render_template('password.html', share_id=share_id, error="Incorrect password or decryption failed")
        return render_template('password.html', share_id=share_id)
    return render_repo_content(repo_data)

def render_repo_content(repo_data):
    expiry = datetime.fromisoformat(repo_data['expiry'])

    if datetime.now() > expiry:
        # Delete expired entry
        db.remove(Query().share_id == repo_data['share_id'])
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

    def fetch_directory_contents(path=''):
        contents_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        contents_resp = requests.get(contents_url, headers=headers)
        
        if contents_resp.status_code == 200:
            contents = contents_resp.json()
            for item in contents:
                if item['type'] == 'dir':
                    item['children'] = fetch_directory_contents(item['path'])
            return contents
        return []

    # Fetch repo contents recursively
    files = fetch_directory_contents()

    response = make_response(render_template('view.html', 
                         readme_content=readme_content,
                         files=files,
                         owner=owner,
                         repo=repo,
                         share_id=repo_data['share_id']))
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response

# Download ZIP route
@app.route('/download/<share_id>')
def download_repo(share_id):
    q = Query()
    repo_data = db.search(q.share_id == share_id)

    if not repo_data:
        abort(404)
    if datetime.now() > datetime.fromisoformat(repo_data[0]['expiry']):
        db.remove(q.share_id == share_id)
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

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
