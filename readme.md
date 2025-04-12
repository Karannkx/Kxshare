KxShare 🚀

Securely share GitHub repositories with optional password protection, expiry dates, and a sharable QR code. Hosted version available at:

https://kxshare.onrender.com


---

Features ✨

Token-based access to private repositories

Password protection for links

Set expiry date for access

QR code generation for quick sharing

Markdown rendering of README

In-browser repo file viewer

Download as ZIP functionality



---

Demo Link 🔗

Live Site: kxshare.onrender.com


---

Setup Instructions (Local Development) ⚙️

> ℹ️ Already deployed at kxshare.onrender.com. The steps below are only if you want to run or modify it locally.



1. Clone the repository

git clone https://github.com/your-username/repo-sharer.git
cd repo-sharer

2. Create a .env file

SECRET_KEY=your-secret-key

3. Install dependencies

pip install -r requirements.txt

4. Run the app

python main.py

Visit http://localhost:5000


---

Deployment (Render) 🚀

1. Go to render.com


2. Create a new Web Service


3. Connect your GitHub repo


4. Set build command: pip install -r requirements.txt


5. Set run command: python main.py


6. Add environment variable:

SECRET_KEY=your-secret-key




Done! Your site will be live on a render URL like https://your-app-name.onrender.com


---

Meta Tags for SEO and Social Sharing 🧠

Add the following to your <head> inside templates/base.html (or similar):

<meta property="og:title" content="GitHub Repo Sharer">
<meta property="og:description" content="Securely share GitHub repos with expiry, password protection, and QR.">
<meta property="og:url" content="{{ request.url }}">
<meta property="og:image" content="{{ url_for('static', filename='preview.png', _external=True) }}">


---

Google Analytics Integration 📈

Paste your GA tracking script inside base.html before the closing </head> tag:

<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>

Replace G-XXXXXXXXXX with your actual GA Measurement ID.


---

License 📄

MIT License. Feel free to fork, share, and contribute!


---

Author

Made with passion by @your-username
GitHub

