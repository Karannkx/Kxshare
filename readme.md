# ⚡ KXShare — GitHub Repo Sharer

A secure and simple way to share GitHub repositories with optional **expiry**, **password protection**, and **QR code** support. Perfect for quick, temporary access with privacy.

## 🚀 Features

- Encrypted **GitHub token** storage
- Optional **password protection**
- Set custom **expiry duration**
- Shareable **unique link** for clients/Resume and other without collab
- **QR code** generation for link sharing
- Auto-expiry and auto-delete
- View **README** and repository files
- One-click **ZIP download**
- Mobile-friendly UI

---

## 🛠 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/karannkx/pvt_repo_accessor.git
cd pvt_repo_accessor
```

### 2. Create a `.env` File

```env
SECRET_KEY=your_super_secret_key_here
```

Make sure this key is strong and private.

---

## ⚙️ Run the App Locally

```bash
pip install -r requirements.txt
python main.py
```

Then visit:  
`http://localhost:5000`

---

## 🌐 Deployment

This project is already hosted on **Render**:  
[https://kxshare.onrender.com](https://kxshare.onrender.com)

To deploy your own:

1. Push the repo to GitHub  
2. Create a new Web Service on [Render](https://render.com/)  
3. Add `SECRET_KEY` in Render environment variables  
4. Set the Build and Start Commands:

```txt
Build Command: pip install -r requirements.txt
Start Command: python main.py
```

---

## 🧠 How It Works

1. **Submit** your GitHub repo URL and token.
2. Token is **encrypted** and stored.
3. A **unique link** is generated (with QR and expiry).
4. Optionally set a **password**.
5. Share the link — viewer can **see README**, **browse files**, and **download ZIP**.

---

## 🔒 Tech Used

- Flask
- TinyDB
- GitHub API
- qrcode
- Markdown
- Cryptography (Fernet AES)
- Render (Deployment)

---

## ✨ Example

Live Demo:  
[https://kxshare.onrender.com](https://kxshare.onrender.com)

---

## Demo Video

Watch the quick demo of GitHub Repo Sharer in action:

[![Watch the demo](https://img.youtube.com/vi/JdDakuW75KY/hqdefault.jpg)](https://youtube.com/shorts/JdDakuW75KY?feature=share)

---

## 📄 License

MIT License © 2025  
Developed by @Karannkx
