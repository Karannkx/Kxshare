import os
import base64
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, make_response, session
from flask_caching import Cache
import qrcode
import base64
from io import BytesIO
from pymongo import MongoClient
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests
from dotenv import load_dotenv
import markdown
import io
import zipfile
from flask import send_from_directory
import google.generativeai as genai

# Load environment variables first
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Initialize MongoDB
client = MongoClient(MONGO_URI)
db = client['kxshare_db']
shares_collection = db['shares']

# Initialize Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')

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

# Homepage route (Landing page with security banner)
@app.route('/')
def landing():
    return render_template('landing.html')

# Create share link page
@app.route('/create', methods=['GET', 'POST'])
def home():
    saved_token = session.get('saved_token', '')
    
    if request.method == 'POST':
        token = request.form['token']
        repo_url = request.form['repo_url']
        expiry_days = int(request.form['expiry_days'])
        protection_password = request.form.get('protection_password', '')
        save_token = request.form.get('save_token', '')
        
        # Save token in session if requested
        if save_token == 'yes':
            session['saved_token'] = token

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

        # Encrypt owner and repo names
        encrypted_owner = cipher.encrypt(owner.encode()).decode()
        encrypted_repo = cipher.encrypt(repo.encode()).decode()

        # Store in MongoDB with all data encrypted
        shares_collection.insert_one({
            'share_id': share_id,
            'encrypted_token': encrypted_token.decode(),
            'encrypted_owner': encrypted_owner,
            'encrypted_repo': encrypted_repo,
            'created_at': datetime.now().isoformat(),
            'expiry': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
            'is_protected': bool(protection_password),
            'password': encrypted_password.decode() if encrypted_password else ''
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

    response = make_response(render_template('home.html', saved_token=saved_token))
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response

# View repository route (updated for encrypted passwords)
@app.route('/view/<share_id>', methods=['GET', 'POST'])
def view_repo(share_id):
    repo_data = shares_collection.find_one({'share_id': share_id})

    if not repo_data:
        abort(404)
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
        shares_collection.delete_one({'share_id': repo_data['share_id']})
        return render_template('expired.html')

    # Decrypt token, owner, and repo
    token = cipher.decrypt(repo_data['encrypted_token'].encode()).decode()
    owner = cipher.decrypt(repo_data['encrypted_owner'].encode()).decode()
    repo = cipher.decrypt(repo_data['encrypted_repo'].encode()).decode()

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
                         share_id=repo_data['share_id'],
                         has_gemini=bool(GEMINI_API_KEY)))
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response

# Generate AI-powered README using Gemini
def generate_ai_readme(owner, repo, token, headers):
    """Analyze repository code and generate comprehensive README using Gemini AI"""
    
    # Fetch main code files
    code_files = []
    
    def collect_code_files(path='', depth=0, max_depth=3):
        if depth > max_depth:
            return
        contents_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        resp = requests.get(contents_url, headers=headers)
        
        if resp.status_code == 200:
            items = resp.json()
            for item in items:
                if item['type'] == 'file':
                    # Only analyze code files
                    if any(item['name'].endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb']):
                        file_resp = requests.get(item['download_url'], headers=headers)
                        if file_resp.status_code == 200:
                            code_files.append({
                                'name': item['name'],
                                'path': item['path'],
                                'content': file_resp.text[:5000]  # Limit to 5000 chars per file
                            })
                elif item['type'] == 'dir' and not item['name'].startswith('.'):
                    collect_code_files(item['path'], depth + 1, max_depth)
    
    collect_code_files()
    
    if not code_files:
        return ""
    
    # Build prompt for Gemini
    code_summary = f"Repository: {owner}/{repo}\n\n"
    for file in code_files[:10]:  # Limit to 10 files
        code_summary += f"\n--- File: {file['path']} ---\n{file['content']}\n"
    
    prompt = f"""Analyze this code repository and generate a comprehensive README.md with the following sections:

1. **Project Title & Description**: Brief overview of what this project does
2. **Features**: Key features and functionality
3. **Tech Stack**: Technologies and frameworks used
4. **Installation & Setup**: Step-by-step instructions to set up the project
5. **Usage**: How to run and use the project
6. **Project Structure**: Brief explanation of file organization
7. **Dependencies**: List of required dependencies

Repository Code:
{code_summary}

Generate a well-formatted markdown README.md file."""
    
    try:
        response = gemini_model.generate_content(prompt)
        return markdown.markdown(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return ""

# Download ZIP route
@app.route('/download/<share_id>')
def download_repo(share_id):
    repo_data = shares_collection.find_one({'share_id': share_id})

    if not repo_data:
        abort(404)
    if datetime.now() > datetime.fromisoformat(repo_data['expiry']):
        shares_collection.delete_one({'share_id': share_id})
        abort(404)

    # Decrypt token, owner, and repo
    token = cipher.decrypt(repo_data['encrypted_token'].encode()).decode()
    owner = cipher.decrypt(repo_data['encrypted_owner'].encode()).decode()
    repo = cipher.decrypt(repo_data['encrypted_repo'].encode()).decode()

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

# AI README generation route (on-demand)
@app.route('/generate-ai-readme/<share_id>')
def generate_ai_readme_route(share_id):
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key not configured"}, 500
    
    repo_data = shares_collection.find_one({'share_id': share_id})
    
    if not repo_data:
        return {"error": "Share not found"}, 404
    
    # Decrypt token, owner, and repo
    token = cipher.decrypt(repo_data['encrypted_token'].encode()).decode()
    owner = cipher.decrypt(repo_data['encrypted_owner'].encode()).decode()
    repo = cipher.decrypt(repo_data['encrypted_repo'].encode()).decode()
    
    headers = {'Authorization': f'token {token}'}
    
    try:
        ai_readme = generate_ai_readme(owner, repo, token, headers)
        return {"success": True, "readme": ai_readme}
    except Exception as e:
        return {"error": str(e)}, 500

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

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
