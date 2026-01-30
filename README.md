# AI Social Media Automation Platform

A complete **SaaS web application** for AI-powered social media content generation and scheduling. Built for non-technical users - everything is manageable through the browser UI.

🚀 **Think: "Canva, but for AI-generated social posts"**

![React](https://img.shields.io/badge/React-18.2-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-cyan.svg)
![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)

---

## ✨ Features

### For Users (Non-Technical)
- **🔐 User Accounts**: Sign up, login, manage your profile
- **🔑 API Key Management**: Enter your own API keys through the UI
- **✨ AI Content Generation**: Enter a topic, get platform-specific content
- **🎨 Tone Selection**: Professional, Casual, Educational, Inspirational
- **📱 Multi-Platform**: LinkedIn, Instagram, Facebook
- **📅 Scheduling**: Pick date/time for auto-posting
- **📊 Dashboard**: See stats, upcoming posts, connection status

### For Developers
- **🔒 Encrypted API Keys**: User keys encrypted with Fernet (AES-256)
- **👥 Multi-User Architecture**: Complete user isolation
- **🔄 Background Scheduler**: Auto-posts with retry logic
- **📝 Full REST API**: Documented at `/docs`
- **🎯 Clean Codebase**: Modular, extensible, well-commented

---

## 📂 Project Structure

```
ai_social_webapp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── auth.py              # JWT authentication
│   │   ├── config.py            # Environment config
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── encryption.py        # API key encryption
│   │   ├── models.py            # User, ApiKey, Post models
│   │   ├── scheduler.py         # Background posting
│   │   ├── routes/
│   │   │   ├── auth.py          # Register, login, profile
│   │   │   ├── api_keys.py      # Key management
│   │   │   ├── generate.py      # Content generation
│   │   │   └── schedule.py      # Post management
│   │   └── services/
│   │       ├── llm_client.py    # OpenAI integration
│   │       ├── linkedin_service.py
│   │       ├── instagram_service.py
│   │       └── facebook_service.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js        # API client
│   │   ├── components/
│   │   │   └── Layout.jsx       # App layout
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── GeneratePage.jsx
│   │   │   ├── PostsPage.jsx
│   │   │   └── SettingsPage.jsx
│   │   ├── App.jsx              # Main app + auth
│   │   └── main.jsx             # Entry point
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### 1. Clone the Project

```bash
cd d:\AI_Social_Media_Automation
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and set SECRET_KEY (required)
```

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Open the App

Navigate to **http://localhost:3000**

1. **Register** a new account
2. Go to **Settings** → Add your **OpenAI API key**
3. Go to **Generate** → Enter a topic → Generate content!
4. Review and **Approve** or **Schedule** your posts

---

## 🔑 User Workflow

### 1. Create Account
- Visit `/register`
- Enter email and password
- You're logged in!

### 2. Add API Keys (Settings Page)
- Click **Settings** in navigation
- Add your **OpenAI API key** (required for generation)
- Optionally add LinkedIn/Instagram/Facebook tokens for real posting

### 3. Generate Content
- Click **Generate**
- Enter your topic (e.g., "5 Tips for Learning Python")
- Select platforms (LinkedIn, Instagram, Facebook)
- Choose tone (Professional, Casual, Educational, Inspirational)
- Click **Generate Content**

### 4. Review & Schedule
- Preview each generated post
- Edit if needed
- Click **Approve Now** or **Schedule** for a specific time

### 5. Monitor Posts
- View all posts in **Posts** page
- Filter by status (Draft, Scheduled, Posted, Failed)
- Retry failed posts
- Cancel scheduled posts

---

## 📊 Database Schema

```
┌────────────┐     ┌──────────────┐     ┌───────────────┐
│   users    │────<│ user_api_keys│     │    topics     │
├────────────┤     ├──────────────┤     ├───────────────┤
│ id         │     │ id           │     │ id            │
│ email      │     │ user_id (FK) │     │ user_id (FK)  │
│ password   │     │ key_type     │     │ name          │
│ full_name  │     │ encrypted_key│     │ tone          │
│ is_active  │     │ is_valid     │     │ created_at    │
│ is_admin   │     │ last_used    │     └───────┬───────┘
└────────────┘     └──────────────┘             │
                                                │
                   ┌───────────────────────────────────────┐
                   │           generated_posts              │
                   ├───────────────────────────────────────┤
                   │ id, user_id, topic_id                 │
                   │ platform, content, hashtags, tone     │
                   │ status (draft/pending/posted/failed)  │
                   │ scheduled_time, posted_at             │
                   │ retry_count, last_error               │
                   └───────────────────────────────────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │          error_logs             │
                   ├─────────────────────────────────┤
                   │ id, post_id, error_message      │
                   │ attempt_number, created_at      │
                   └─────────────────────────────────┘
```

---

## 🔒 Security

| Feature | Implementation |
|---------|----------------|
| Passwords | bcrypt hashing |
| API Keys | Fernet encryption (AES-256) |
| Authentication | JWT tokens |
| User Isolation | All data filtered by user_id |
| CORS | Configured for frontend origin |

### Generating Encryption Key

```python
# Run in Python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Use this in your `.env` as `ENCRYPTION_KEY`.

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, get JWT |
| GET | `/api/auth/me` | Get profile |
| PUT | `/api/auth/me` | Update profile |

### API Keys
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/keys/status` | Check which keys configured |
| GET | `/api/keys/` | List all keys (masked) |
| POST | `/api/keys/` | Add new key |
| PUT | `/api/keys/{id}` | Update key |
| DELETE | `/api/keys/{id}` | Delete key |
| POST | `/api/keys/{id}/test` | Test key validity |

### Content Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate/` | Generate content |
| GET | `/api/generate/topics` | List topics |
| GET | `/api/generate/topics/{id}` | Get topic + posts |

### Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posts/` | List posts |
| GET | `/api/posts/stats` | Get statistics |
| GET | `/api/posts/upcoming` | Scheduled posts |
| POST | `/api/posts/{id}/approve` | Approve + schedule |
| POST | `/api/posts/{id}/cancel` | Cancel scheduled |
| POST | `/api/posts/{id}/retry` | Retry failed |
| DELETE | `/api/posts/{id}` | Delete post |

---

## 🚀 Deployment

### Option 1: Docker (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Option 2: Railway/Render

1. Deploy backend as Python app
2. Deploy frontend as static site
3. Add PostgreSQL addon
4. Set environment variables

---

## 📈 Converting to Paid SaaS

### 1. Add Stripe Integration
```python
# backend/app/routes/billing.py
# - Create checkout sessions
# - Handle webhooks
# - Track subscription status
```

### 2. Add User Tiers
```python
class User(Base):
    tier = Column(String, default="free")  # free, pro, enterprise
    posts_this_month = Column(Integer, default=0)
```

### 3. Add Rate Limiting
```python
# Check tier limits before generation
if user.tier == "free" and user.posts_this_month >= 10:
    raise HTTPException(402, "Upgrade to Pro for more posts")
```

### 4. Add More Platforms
- Copy `linkedin_service.py` as template
- Add new `ApiKeyType`
- Add UI in Settings page

---

## 🔧 Adding New Platforms

1. **Create Service** (`backend/app/services/twitter_service.py`)
2. **Add ApiKeyType** in `models.py`
3. **Add Platform Enum** in `models.py`
4. **Add to Scheduler** in `scheduler.py`
5. **Add UI** in Settings and Generate pages

---

## 📝 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key |
| `ENCRYPTION_KEY` | ✅ | API key encryption |
| `DATABASE_URL` | ✅ | PostgreSQL or SQLite |
| `FRONTEND_URL` | ❌ | CORS origin |
| `DEBUG` | ❌ | Enable debug mode |

---

## 🤝 Support

This is a complete, production-ready MVP. For questions:
- Check API docs at `http://localhost:8000/docs`
- Review code comments
- Check error logs in Posts page

---

Built with ❤️ for content creators
