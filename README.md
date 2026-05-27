
```markdown
# 📖 Ink & Page - Read & Write Online

![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.3.3-red)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

## ✨ About

Ink & Page is a beautiful web platform where readers discover stories and writers share their creativity. Read books, write your own stories, and connect with a community of book lovers.

### Features

**Readers** 📚
- Browse library of stories
- Search by title/author/genre
- Like and comment on stories

**Writers** ✍️
- Create and publish stories
- Save drafts
- Get daily writing prompts
- Track views and likes

## 🚀 Quick Setup

### 1. Install Python
Download Python 3.8+ from [python.org](https://python.org)

### 2. Download Files
Save these 3 files in one folder:
- `app.py` - Backend server
- `models.py` - Database
- `index.html` - Website

### 3. Install Dependencies

Open terminal in your folder and run:
```bash
pip install Flask Flask-CORS Flask-SQLAlchemy Flask-JWT-Extended bcrypt
```

### 4. Run the Server

```bash
python app.py
```

### 5. Open Website

Go to: `http://127.0.0.1:5000`

## 📁 File Structure

```
your-folder/
├── app.py          # Backend (Flask)
├── models.py       # Database models
├── index.html      # Frontend
└── inkpage.db      # Database (auto-created)
```

## 🔌 API Endpoints

| Action | Endpoint | Method |
|--------|----------|--------|
| Register | `/api/register` | POST |
| Login | `/api/login` | POST |
| Get stories | `/api/stories` | GET |
| Create story | `/api/stories` | POST |
| Like story | `/api/stories/1/like` | POST |
| Add comment | `/api/stories/1/comments` | POST |

## 🧪 Test the App

**Demo Login** (no backend needed):
- Any email/password works

**With Backend**:
1. Click "Create account"
2. Enter username, email, password
3. Start writing!

## 🎨 Quick Customization

**Change colors** - In `index.html`, find and replace:
```css
background: #d98e46;  /* Orange accent color */
```

**Change site name**:
```html
<div class="logo">Your Name Here</div>
```

## 🐛 Common Issues

**404 Error?** 
- Make sure you're at `http://127.0.0.1:5000` not just file path

**Module not found?**
- Run: `pip install flask`

**Port in use?**
- Change port in `app.py`: `port=5001`

## 🚀 Deploy Online

**Free Options:**

1. **PythonAnywhere** (easiest)
   - Upload files
   - Set up web app with Flask

2. **Render.com**
   - Push to GitHub
   - Create Web Service
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`

## 💡 Tips

- Use **demo mode** to test without installing backend
- Save **drafts** while writing
- Check **daily prompts** for inspiration
- **Like and comment** to support other writers

## 📝 License

MIT - Free to use and modify

## 🙏 Support

- Report issues on GitHub
- Email: support@inkpage.com

---

## ⚡ One-Line Commands

```bash
# Install everything
pip install Flask Flask-CORS Flask-SQLAlchemy Flask-JWT-Extended bcrypt

# Run server
python app.py

# Stop server
Press Ctrl+C
```

---

**Happy Reading & Writing! 📖✨**
```

This shorter README includes all essential information while being concise and easy to read. Perfect for quick setup!
