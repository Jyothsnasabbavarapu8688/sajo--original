# ⚡ SAJO - Modern Knowledge Workspace

SAJO is a production-ready SaaS platform that helps users transform long text and documents into structured knowledge. It features an ultra-modern, futuristic UI with animations, real-time collaboration, workspaces, and powerful content processing tools.

---

## 🚀 Features

*   **Dynamic Knowledge Extraction:** Instantly generate summaries, key concepts, bullet points, highlights, and quizzes from raw text or document uploads.
*   **File Upload Support:** Upload and extract content seamlessly from `.pdf`, `.docx`, and `.txt` files.
*   **Real-Time Collaboration:** Team workspaces allow multiple users to edit documents simultaneously, powered by WebSockets.
*   **Multi-Role Team Management:** Invite users as Viewers, Editors, or Owners to manage secure team spaces.
*   **Interactive Learning Tools:** Auto-generate multiple-choice quizzes and dynamic flashcards.
*   **Intelligent Q&A Chat:** Ask specific questions about your processed content in a familiar chat interface.
*   **Deep Personalization:** Fully customizable themes (Dark, Light, Midnight, Neon), avatars, and account settings.
*   **Auto-Save & History:** Never lose an idea thanks to background auto-saves and a complete searchable history log.
*   **Export Options:** Instantly export generated insights to PDF, Markdown, or raw TXT.

---

## 🛠️ Tech Stack

*   **Backend:** Python, Flask, Flask-SocketIO (for WebSockets/collaboration).
*   **Database:** SQLite (with robust schemas for users, workspaces, saved items, history).
*   **Frontend:** Vanilla HTML, CSS (`style.css`), JavaScript (`script.js`) — completely bespoke modern UI.
*   **LLM API:** Groq (handled securely behind the backend). 
*   **Deployment:** Docker, docker-compose ready.

---

## 📦 Getting Started (Local Development)

### Prerequisites
*   Python 3.9+
*   Git

### 1. Clone & Set Up Virtual Environment

```bash
git clone <repository_url>
cd sajo
python -m venv venv
```

**Activate Environment:**
*   Windows: `.\venv\Scripts\activate`
*   Mac/Linux: `source venv/bin/activate`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Add API Keys
Create a `.env` file in the root directory and add your Groq API key:
```env
FLASK_ENV=development
SECRET_KEY=generate_a_secure_random_key_here
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 4. Run the Application
Start the Flask/Eventlet WebSocket server:
```bash
python app.py
```

The application will now be running smoothly at: `http://127.0.0.1:5000`

---

## 🐳 Running with Docker

You can easily containerize SAJO using the provided Docker files:

```bash
docker-compose up --build
```
This will start the application locally using Docker, mapping port 5000 to your host machine.

---

## 🗂️ Project Structure

```
📁 SAJO/
 ├── app.py                   # Core backend application and endpoints
 ├── database.db              # SQLite Database
 ├── requirements.txt         # Python dependencies
 ├── Dockerfile               # Container build configuration
 ├── docker-compose.yml       # Local container orchestration
 ├── 📁 static/
 │   ├── style.css            # Complete design system
 │   ├── script.js            # Core interactive logic
 │   └── 📁 avatars/          # User-uploaded profile pictures
 ├── 📁 templates/
 │   ├── landing.html         # Public hero landing page
 │   ├── login.html           # Authentication UI
 │   ├── register.html        # Registration UI
 │   ├── dashboard.html       # Main content processor
 │   ├── library.html         # Saved knowledge items
 │   ├── workspace.html       # Team management & collaboration
 │   ├── profile.html         # Account profile & credentials
 │   ├── settings.html        # Themes and preferences
 │   └── history.html         # Activity tracking log
 └── 📁 uploads/              # Temporary space for document parsing
```

## 🔒 Security Notes
- Passwords are hashed using Werkzeug.
- Filenames and sessions are rigorously sanitized to prevent injection attacks.
- Real-time endpoints are bound to workspace permissions.

---
_Owner: Jyothsna_
