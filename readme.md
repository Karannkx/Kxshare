# ⚡ KXShare — AI-Powered Secure GitHub Repository Sharer

> **Share private GitHub repositories securely with encrypted tokens, password protection, QR codes, and AI-powered README generation using Gemini AI.**

[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-green?style=for-the-badge&logo=mongodb)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://www.docker.com/)

---

## 🌟 Features

### 🔐 Security First
- **AES-256 Encryption** for GitHub tokens and passwords
- **PBKDF2** key derivation with 100k iterations
- Optional **password protection** for shared links
- **Auto-expiry** with automatic cleanup
- Encrypted storage of repository credentials

### 📦 Sharing Made Easy
- **Unique shareable links** with custom expiry (1-365 days)
- **QR code generation** for instant mobile access
- **One-click ZIP download** of entire repositories
- **File browser** with syntax highlighting
- Mobile-responsive neo-brutalist UI

### 🤖 AI-Powered Features
- **Gemini AI** integration for README generation
- Automatic code analysis and documentation
- Smart dependency detection
- Technology stack identification

### 🎨 Modern UI/UX
- Neo-brutalist design with GSAP animations
- Responsive 3-column form layout (laptop optimized)
- Floating stickers and interactive elements
- Privacy popup with smooth animations
- Dark mode ready

### 🔗 Developer Friendly
- Session-based token saving (optional)
- RESTful API endpoints
- Docker containerization
- MongoDB for scalable data storage
- SEO optimized (robots.txt, sitemap.xml)

---

## 🏗️ Architecture

```
┌─────────────┐     Encrypted     ┌──────────────┐
│   Client    │ ─────Token────────▶│   KXShare    │
│  (Browser)  │                    │  Flask App   │
└─────────────┘                    └──────┬───────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              ┌──────────┐          ┌──────────┐         ┌──────────┐
              │ MongoDB  │          │ GitHub   │         │ Gemini   │
              │ Database │          │   API    │         │   AI     │
              └──────────┘          └──────────┘         └──────────┘
```

### Tech Stack

**Backend:**
- Python 3.11+ with Flask
- MongoDB (migrated from TinyDB)
- Cryptography (Fernet AES-256)
- PyMongo for database operations

**Frontend:**
- GSAP 3.12.2 for animations
- FontAwesome icons
- Space Grotesk & Space Mono fonts
- Responsive CSS Grid

**APIs:**
- GitHub REST API v3
- Google Gemini AI (gemini-2.5-flash)

**Infrastructure:**
- Docker & Docker Compose
- Render (Production deployment)
- MongoDB Atlas (Cloud database option)

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/karannkx/pvt_repo_accessor.git
cd pvt_repo_accessor

# Create .env file
cat > .env << EOF
SECRET_KEY=your_super_secret_key_change_this_to_something_secure
GEMINI_API_KEY=your_gemini_api_key_optional
EOF

# Start with Docker Compose
docker-compose up -d

# Visit http://localhost:5000
```

**Services Started:**
- 🌐 KXShare App: `http://localhost:5000`
- 🍃 MongoDB: `localhost:27017`

**Stop Services:**
```bash
docker-compose down
```

**View Logs:**
```bash
docker-compose logs -f kxshare_app
```

### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/karannkx/pvt_repo_accessor.git
cd pvt_repo_accessor

# Install MongoDB locally (macOS)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "SECRET_KEY=your_secret_key" > .env
echo "MONGO_URI=mongodb://localhost:27017/" >> .env
echo "GEMINI_API_KEY=your_gemini_key" >> .env

# Run application
python main.py
```

---

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Encryption key for tokens/passwords | ✅ Yes | - |
| `MONGO_URI` | MongoDB connection string | ✅ Yes | `mongodb://localhost:27017/` |
| `GEMINI_API_KEY` | Google Gemini API key | ❌ No | - |

**Security Note:** Use a strong `SECRET_KEY` (minimum 32 characters). Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🐳 Docker Configuration

### Dockerfile Highlights
- Base image: `python:3.11-slim`
- Multi-stage caching for dependencies
- Minimal attack surface
- Runs on port 5000

### docker-compose.yml Services
- **kxshare_app**: Main Flask application
- **mongodb**: MongoDB 7.0 with health checks
- **Volumes**: Persistent MongoDB data storage
- **Networks**: Isolated bridge network

### Build Custom Image
```bash
docker build -t kxshare:latest .
docker run -p 5000:5000 --env-file .env kxshare:latest
```

---

## 🎯 Usage Guide

### 1. Get GitHub Personal Access Token
- Go to GitHub Settings → Developer Settings
- Personal Access Tokens → Tokens (classic)
- Generate new token with `repo` scope
- Copy token (starts with `ghp_`)

### 2. Create Share Link
1. Visit KXShare homepage
2. Enter repository URL (e.g., `https://github.com/user/repo`)
3. Paste GitHub token
4. Set expiry duration (1-365 days)
5. Optional: Add password protection
6. Click "Generate Secure Link"

### 3. Share & Access
- Copy generated link or scan QR code
- Recipients can view README, browse files, download ZIP
- Password-protected links require authentication
- Links auto-expire after set duration

---

## 📂 Project Structure

```
pvt_repo_accessor/
├── main.py                 # Flask application & routes
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Multi-container setup
├── .dockerignore          # Docker build exclusions
├── .env                   # Environment variables (create this)
├── templates/             # Jinja2 HTML templates
│   ├── landing.html      # Landing page
│   ├── home.html         # Main form (dashboard)
│   ├── success.html      # Link generation success
│   ├── view.html         # Repository viewer
│   ├── password.html     # Password protection gate
│   ├── expired.html      # Expired link page
│   └── privacy.html      # Privacy policy
├── static/
│   ├── robots.txt        # SEO crawler rules
│   └── sitemap.xml       # Site structure
└── README.md             # This file
```

---

## 🔄 Migration Notes

### TinyDB → MongoDB
**Previous:** File-based JSON storage with TinyDB
**Current:** MongoDB for scalability and concurrent access

**Why MongoDB?**
- ✅ Better performance with encryption operations
- ✅ Horizontal scaling support
- ✅ Rich query capabilities
- ✅ Cloud-ready (MongoDB Atlas)
- ✅ Automatic TTL indexes for expiry

**Data Schema:**
```json
{
  "share_id": "uuid-string",
  "encrypted_token": "base64-encrypted-token",
  "encrypted_owner": "base64-encrypted-owner",
  "encrypted_repo": "base64-encrypted-repo",
  "created_at": "2026-02-24T10:30:00",
  "expiry": "2026-03-26T10:30:00",
  "is_protected": true,
  "password": "base64-encrypted-password"
}
```

---

## 🌐 Deployment

### Render (Current Production)
1. Fork this repository
2. Create new Web Service on [Render](https://render.com)
3. Connect GitHub repository
4. Add environment variables:
   - `SECRET_KEY`
   - `MONGO_URI` (use MongoDB Atlas)
   - `GEMINI_API_KEY`
4. Deploy with:
   ```
   Build: pip install -r requirements.txt
   Start: python main.py
   ```

### MongoDB Atlas Setup
1. Create free cluster at [MongoDB Atlas](https://cloud.mongodb.com)
2. Whitelist Render IP or use `0.0.0.0/0` (less secure)
3. Create database user
4. Copy connection string to `MONGO_URI`

### Docker Production
```bash
# Use external MongoDB
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/ docker-compose up -d

# Or modify docker-compose.yml for production
```

---

## 🔒 Security Best Practices

1. **Never commit `.env`** - Add to `.gitignore`
2. **Rotate SECRET_KEY** regularly
3. **Use MongoDB Atlas** with IP whitelisting
4. **Set strong passwords** for protected links
5. **Monitor access logs** for suspicious activity
6. **Update dependencies** regularly
7. **Use HTTPS** in production (Render provides this)

---

## 🤝 Contributing

**🎉 KXShare is now open sourced!** We welcome contributions from the community.

Contributions welcome! This project is **open source** and available for everyone to contribute.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

**Ideas for contributions:**
- Code review AI integration
- Analytics dashboard
- Rate limiting
- Email notifications
- Custom link aliases

---

## 📊 Roadmap

- [x] MongoDB migration
- [x] Docker containerization
- [x] AI README generation
- [x] Neo-brutalist UI redesign
- [ ] Analytics dashboard
- [ ] Code review AI
- [ ] Email notifications
- [ ] Custom domains
- [ ] API rate limiting
- [ ] Multi-language support

---

## 📄 License

MIT License © 2025-2026

**Developed with 💙 by [@Karannkx](https://github.com/Karannkx)**

**Connect:**
- [GitHub](https://github.com/Karannkx)
- [LinkedIn](https://linkedin.com/in/Karannkx)
- [Instagram](https://instagram.com/Karannkx)

---

## ⚠️ Disclaimer

**⚠️ IMPORTANT:** Using this tool without proper authorization is **NOT ALLOWED**. You must have:
- Permission to access and share the repositories
- Valid GitHub token with appropriate scopes
- Authorization from repository owners

Unauthorized use or distribution of private repositories is a violation of GitHub's Terms of Service and may be illegal.

---

This tool is for **legitimate repository sharing** only. Users are responsible for:
- Securing their GitHub tokens
- Respecting repository licenses
- Not sharing unauthorized content
- Following GitHub's Terms of Service
- Obtaining proper permissions before sharing

KXShare encrypts and protects your data but is provided "as-is" without warranties.

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ for the open-source community

[Report Bug](https://github.com/Karannkx/pvt_repo_accessor/issues) · [Request Feature](https://github.com/Karannkx/pvt_repo_accessor/issues)

</div>
