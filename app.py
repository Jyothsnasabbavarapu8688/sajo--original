import os
import json
import uuid
import datetime
import logging
import sqlite3
import markdown
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file, abort
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from groq import Groq
import PyPDF2
from docx import Document as DocxDocument
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "sajo_elite_production_final_2026")
socketio = SocketIO(app, cors_allowed_origins="*")

# Custom Filters
@app.template_filter('from_json')
def from_json_filter(s):
    try:
        return json.loads(s)
    except:
        return []


# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API Clients
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ============================================
# DATABASE & ARCHITECTURE (ELITE)
# ============================================
DB_PATH = 'database.db'

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn


# ============================================
# SECURITY & MIDDLEWARE
# ============================================
user_requests = {} # Simple in-memory rate limiter

def limit_rate(limit=10, window=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            uid = session.get('user_id', request.remote_addr)
            now = datetime.datetime.now()
            if uid not in user_requests: user_requests[uid] = []
            user_requests[uid] = [t for t in user_requests[uid] if (now - t).seconds < window]
            if len(user_requests[uid]) >= limit: return jsonify({'error': 'Rate limit exceeded'}), 429
            user_requests[uid].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# UTILS & LOGGING
# ============================================
def log_activity(user_id, action, details):
    conn = get_db()
    try:
        conn.execute('INSERT INTO ActivityLogs (user_id, action, details) VALUES (?, ?, ?)', (user_id, action, details))
        conn.commit()
    except Exception as e:
        print(f"FAILED TO LOG ACTIVITY: {e}")
    finally:
        conn.close()


# ============================================
# ROUTES - PAGES (PRODUCTION READY)
# ============================================

@app.route('/')
def landing_page(): return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        conn = get_db()
        # Allow login by either email or username
        user = conn.execute('SELECT * FROM Users WHERE email = ? OR username = ?', 
                           (request.form['email'], request.form['email'])).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], request.form['password']):
            session.update({'user_id': user['id'], 'username': user['username']})

            log_activity(user['id'], "Login", "User logged in successfully")
            return redirect(url_for('dashboard_page'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        pw = generate_password_hash(request.form['password'])
        conn = get_db()
        try:
            cursor = conn.execute('INSERT INTO Users (username, email, password) VALUES (?, ?, ?)',
                         (request.form['username'], request.form['email'], pw))
            user_id = cursor.lastrowid
            
            # Create Default Workspace
            ws_cursor = conn.execute('INSERT INTO Workspaces (name, owner_id) VALUES (?, ?)', ("Primary Workspace", user_id))
            conn.execute('INSERT INTO WorkspaceMembers (workspace_id, user_id, role) VALUES (?, ?, ?)', 
                        (ws_cursor.lastrowid, user_id, 'Owner'))
            
            conn.commit()
            log_activity(user_id, "Registration", "User registered and workspace created")
            return redirect(url_for('login_page'))
        except sqlite3.IntegrityError: flash('Email already exists', 'error')
        except Exception: flash('Registration failed', 'error')
        finally: conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    uid = session.get('user_id')
    if uid: log_activity(uid, "Logout", "User logged out")
    session.clear()
    return redirect(url_for('landing_page'))

@app.route('/forgot-password')
def forgot_password():
    flash('Intelligence recovery system requires SMTP configuration. Contact administrator.', 'info')
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard_page():
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    docs = conn.execute('SELECT * FROM Documents WHERE user_id = ? AND is_deleted = 0 ORDER BY updated_at DESC LIMIT 6', (uid,)).fetchall()
    
    stats = {
        'total_docs': conn.execute('SELECT COUNT(*) FROM Documents WHERE user_id = ? AND is_deleted = 0', (uid,)).fetchone()[0],
        'total_insights': conn.execute('SELECT COUNT(*) FROM KnowledgeGraph g JOIN Documents d ON g.source_doc_id = d.id WHERE d.user_id = ?', (uid,)).fetchone()[0],
        'recent_activity': conn.execute('SELECT COUNT(*) FROM ActivityLogs WHERE user_id = ? AND created_at > date("now", "-7 days")', (uid,)).fetchone()[0]
    }
    
    activities = conn.execute('SELECT * FROM ActivityLogs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', (uid,)).fetchall()
    workspaces = conn.execute('SELECT w.* FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id WHERE m.user_id = ?', (uid,)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, recent_documents=docs, stats=stats, activities=activities, workspaces=workspaces)

@app.route('/getting-started')
def guide_page():
    return render_template('guide.html')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    uid = session['user_id']
    username = request.form.get('username')
    bio = request.form.get('bio')
    
    conn = get_db()
    conn.execute('UPDATE Users SET username = ?, bio = ? WHERE id = ?', (username, bio, uid))
    conn.commit()
    conn.close()
    
    session['username'] = username
    log_activity(uid, "Profile Update", "User intelligence profile updated")
    flash('Intelligence profile persistent.', 'success')
    return redirect(url_for('profile_page'))

@app.route('/workspaces')
@login_required
def workspaces_page():
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    my_ws = conn.execute('''
        SELECT w.*, (SELECT COUNT(*) FROM Documents d WHERE d.workspace_id = w.id AND d.is_deleted = 0) as doc_count 
        FROM Workspaces w WHERE w.owner_id = ?
    ''', (uid,)).fetchall()
    shared_ws = conn.execute('''
        SELECT w.*, u.username as owner_name, (SELECT COUNT(*) FROM Documents d WHERE d.workspace_id = w.id AND d.is_deleted = 0) as doc_count 
        FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id JOIN Users u ON w.owner_id = u.id 
        WHERE m.user_id = ? AND w.owner_id != ?
    ''', (uid, uid)).fetchall()
    conn.close()
    return render_template('workspace.html', user=user, workspaces=my_ws, team_workspaces=shared_ws)

@app.route('/workspace/<int:ws_id>')
@login_required
def workspace_detail(ws_id):
    uid = session['user_id']
    conn = get_db()
    # Check if member
    member = conn.execute('SELECT * FROM WorkspaceMembers WHERE workspace_id = ? AND user_id = ?', (ws_id, uid)).fetchone()
    if not member: return abort(403)
    
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    ws = conn.execute('SELECT * FROM Workspaces WHERE id = ?', (ws_id,)).fetchone()
    docs = conn.execute('SELECT * FROM Documents WHERE workspace_id = ? AND is_deleted = 0 ORDER BY updated_at DESC', (ws_id,)).fetchall()
    workspaces = conn.execute('SELECT w.* FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id WHERE m.user_id = ?', (uid,)).fetchall()
    conn.close()
    return render_template('library.html', user=user, documents=docs, current_workspace=ws, workspaces=workspaces)

@app.route('/library')
@login_required
def library_page():
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    docs = conn.execute('SELECT * FROM Documents WHERE user_id = ? AND is_deleted = 0 ORDER BY updated_at DESC', (uid,)).fetchall()
    saved = conn.execute('SELECT * FROM KnowledgeGraph WHERE source_doc_id IN (SELECT id FROM Documents WHERE user_id = ?)', (uid,)).fetchall()
    workspaces = conn.execute('SELECT * FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id WHERE m.user_id = ?', (uid,)).fetchall()
    conn.close()
    return render_template('library.html', user=user, documents=docs, saved_items=saved, workspaces=workspaces)

@app.route('/history')
@login_required
def history_page():
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    activities = conn.execute('SELECT * FROM ActivityLogs WHERE user_id = ? ORDER BY created_at DESC', (uid,)).fetchall()
    workspaces = conn.execute('SELECT w.* FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id WHERE m.user_id = ?', (uid,)).fetchall()
    conn.close()
    return render_template('history.html', user=user, activities=activities, workspaces=workspaces)

@app.route('/settings')
@login_required
def settings_page():
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    workspaces = conn.execute('SELECT w.* FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id WHERE m.user_id = ?', (uid,)).fetchall()
    conn.close()
    return render_template('settings.html', user=user, workspaces=workspaces)

@app.route('/profile')
@login_required
def profile_page():
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    workspaces = conn.execute('SELECT * FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id WHERE m.user_id = ?', (uid,)).fetchall()
    conn.close()
    return render_template('profile.html', user=user, workspaces=workspaces)

@app.route('/editor')
@login_required
def editor_page():
    doc_id = request.args.get('id')
    uid = session['user_id']
    conn = get_db()
    
    doc = None
    if doc_id:
        # Check if owner OR in the document's workspace
        doc = conn.execute('''
            SELECT d.* FROM Documents d 
            LEFT JOIN WorkspaceMembers m ON d.workspace_id = m.workspace_id AND m.user_id = ?
            WHERE d.id = ? AND (d.user_id = ? OR m.user_id IS NOT NULL)
        ''', (uid, doc_id, uid)).fetchone()
        
    workspaces = conn.execute('SELECT w.* FROM Workspaces w JOIN WorkspaceMembers m ON w.id = m.workspace_id WHERE m.user_id = ?', (uid,)).fetchall()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    conn.close()
    
    if doc_id and not doc: return abort(403)
    return render_template('editor.html', document=doc, workspaces=workspaces, user=user)

# ============================================
# PRODUCTION APIS (REAL FUNCTIONALITY)
# ============================================

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'No file segment'}), 400
    file = request.files['file']
    ws_id = request.form.get('workspace_id')
    if file.filename == '': return jsonify({'error': 'Empty filename'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    text = ""
    try:
        if filename.endswith('.pdf'):
            with open(filepath, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                text = "\n".join([page.extract_text() for page in pdf.pages])
        elif filename.endswith('.docx'):
            doc = DocxDocument(filepath)
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500
        
    return jsonify({'success': True, 'content': text})

@app.route('/api/process-knowledge', methods=['POST'])
@login_required
@limit_rate(limit=10, window=60)
def process_knowledge():
    data = request.json
    content, title, doc_id = data.get('content'), data.get('title'), data.get('id')
    ws_id = data.get('workspace_id')
    uid = session['user_id']
    
    if not content: return jsonify({'error': 'No content provided'}), 400

    try:
        print(f"DEBUG: Processing intelligence for user {uid}")
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": """You are SAJO Intelligence Engine. 
                      Extract elite-level intelligence. Return STRICT JSON: 
                      {
                        "summary": "A deep, professional executive summary (3-4 paragraphs)",
                        "bullets": ["Key insight 1", "Key insight 2", ...],
                        "tags": ["Tag1", "Tag2"],
                        "concepts": [{"name": "Concept", "type": "Topic/Person/Entity"}]
                      }"""}, 
                     {"role": "user", "content": content}],
            response_format={"type": "json_object"}
        )
        print("DEBUG: Groq API response received")
        res = json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"DEBUG: AI ERROR: {e}")
        logging.error(f"AI ERROR: {e}")
        return jsonify({'error': f'Intelligence processing failed: {str(e)}'}), 500

    conn = get_db()
    print(f"DEBUG: Saving to database (doc_id: {doc_id})")

    
    if doc_id:
        doc = conn.execute('SELECT user_id, content FROM Documents WHERE id = ?', (doc_id,)).fetchone()
        if not doc or doc['user_id'] != uid: return jsonify({'error': 'Unauthorized intelligence access'}), 403
        
        conn.execute('INSERT INTO DocumentVersions (document_id, content, version_num) VALUES (?, ?, (SELECT COALESCE(MAX(version_num), 0) + 1 FROM DocumentVersions WHERE document_id = ?))', 
                    (doc_id, doc['content'], doc_id))
        
        conn.execute('UPDATE Documents SET title=?, content=?, summary=?, bullets=?, tags=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?', 
                    (title or "Untitled Intelligence", content, res['summary'], json.dumps(res['bullets']), json.dumps(res['tags']), doc_id, uid))
        log_activity(uid, "Updated Knowledge", f"Title: {title}")
    else:
        cursor = conn.execute('INSERT INTO Documents (title, content, summary, bullets, tags, user_id, workspace_id) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                            (title or "New Intelligence Report", content, res['summary'], json.dumps(res['bullets']), json.dumps(res['tags']), uid, ws_id))
        doc_id = cursor.lastrowid
        log_activity(uid, "Generated New Knowledge", f"Title: {title}")
    
    conn.execute('DELETE FROM KnowledgeGraph WHERE source_doc_id = ?', (doc_id,))
    for concept in res['concepts']:
        linked = conn.execute('SELECT id FROM Documents WHERE user_id = ? AND id != ? AND (title LIKE ? OR content LIKE ?)', 
                             (uid, doc_id, f"%{concept['name']}%", f"%{concept['name']}%")).fetchone()
        conn.execute('INSERT INTO KnowledgeGraph (source_doc_id, concept, relationship, linked_doc_id) VALUES (?, ?, ?, ?)', 
                    (doc_id, concept['name'], concept.get('type', 'Association'), linked['id'] if linked else None))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': doc_id, 'data': res})

@app.route('/api/generate-quiz', methods=['POST'])
@login_required
def generate_quiz():
    data = request.json
    content = data.get('content')
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Generate 3 multiple choice questions from content. Return JSON: {questions: [{question, options: [], answer: index}]}"}, 
                     {"role": "user", "content": content}],
            response_format={"type": "json_object"}
        )
        return jsonify({'success': True, 'data': json.loads(completion.choices[0].message.content)})
    except: return jsonify({'error': 'Quiz generation failed'}), 500

@app.route('/api/search')
@login_required
def global_search():
    q = request.args.get('q', '').lower()
    uid = session['user_id']
    conn = get_db()
    # Search owner docs OR workspace docs where member
    docs = conn.execute('''
        SELECT DISTINCT d.id, d.title, d.summary FROM Documents d
        LEFT JOIN WorkspaceMembers wm ON d.workspace_id = wm.workspace_id AND wm.user_id = ?
        WHERE (d.user_id = ? OR wm.user_id IS NOT NULL) 
        AND (d.title LIKE ? OR d.content LIKE ?) 
        AND d.is_deleted = 0
    ''', (uid, uid, f"%{q}%", f"%{q}%")).fetchall()
    conn.close()
    return jsonify({'results': [dict(d) for d in docs]})

@app.route('/api/query-knowledge', methods=['POST'])
@login_required
def query_knowledge():
    data = request.json
    query, content = data.get('query'), data.get('content')
    if not query: return jsonify({'error': 'No query provided'}), 400
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are the SAJO Intelligence Engine. Your knowledge is strictly bounded by the provided context. Answer user questions concisely and accurately based ONLY on the context."}, 
                     {"role": "user", "content": f"CONTEXT:\n{content}\n\nUSER QUESTION: {query}"}]
        )
        return jsonify({'success': True, 'answer': completion.choices[0].message.content})
    except Exception as e:
        logging.error(f"QUERY ERROR: {e}")
        return jsonify({'error': 'Intelligence query failed'}), 500

@app.route('/api/export/<string:format>/<int:doc_id>')
@login_required
def export_document(format, doc_id):
    uid = session['user_id']
    conn = get_db()
    doc = conn.execute('SELECT * FROM Documents WHERE id = ? AND user_id = ?', (doc_id, uid)).fetchone()
    conn.close()
    
    if not doc: return abort(404)
    
    filename = secure_filename(f"{doc['title']}.{format}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if format == 'md':
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {doc['title']}\n\n{doc['content']}")
    elif format == 'pdf':
        c = canvas.Canvas(filepath, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 750, doc['title'])
        c.setFont("Helvetica", 12)
        text = c.beginText(72, 720)
        # Simple wrapping
        for line in doc['content'].split('\n'):
            text.textLine(line[:80])
        c.drawText(text)
        c.save()
    
    return send_file(filepath, as_attachment=True)

@app.route('/api/analytics')
@login_required
def get_real_analytics():
    uid = session['user_id']
    conn = get_db()
    # Actual daily counts for the last 7 days
    history = conn.execute('''
        SELECT date(created_at) as day, COUNT(*) as count 
        FROM ActivityLogs WHERE user_id = ? 
        GROUP BY day ORDER BY day DESC LIMIT 7
    ''', (uid,)).fetchall()
    conn.close()
    labels = [r['day'] for r in history]
    data = [r['count'] for r in history]
    return jsonify({'labels': labels, 'data': data})

@app.route('/api/knowledge-graph/<int:doc_id>')
@login_required
def get_graph_data(doc_id):
    conn = get_db()
    rels = conn.execute('SELECT concept as id, relationship as label, linked_doc_id FROM KnowledgeGraph WHERE source_doc_id = ?', (doc_id,)).fetchall()
    conn.close()
    
    nodes = [{'id': 'ROOT', 'name': 'Source Intelligence', 'val': 20, 'type': 'root'}]
    links = []
    for r in rels:
        nodes.append({'id': r['id'], 'name': r['id'], 'val': 10, 'linked_doc': r['linked_doc_id']})
        links.append({'source': 'ROOT', 'target': r['id'], 'label': r['label']})
    
    return jsonify({'nodes': nodes, 'links': links})

@app.route('/api/history/clear')
@login_required
def clear_history():
    uid = session['user_id']
    conn = get_db()
    conn.execute('DELETE FROM ActivityLogs WHERE user_id = ?', (uid,))
    conn.commit()
    conn.close()
    return redirect(url_for('history_page'))

@app.route('/api/autosave', methods=['POST'])
@login_required
def api_autosave_v2():
    data = request.json
    doc_id = data.get('id')
    content = data.get('content')
    uid = session['user_id']
    if not doc_id: return jsonify({'success': False})
    
    conn = get_db()
    conn.execute('UPDATE Documents SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?', (content, doc_id, uid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/workspace/create', methods=['POST'])
@login_required
def create_workspace():
    data = request.json
    name = data.get('name')
    icon = data.get('icon', '📁')
    desc = data.get('description', '')
    uid = session['user_id']
    
    conn = get_db()
    cursor = conn.execute('INSERT INTO Workspaces (name, icon, description, owner_id) VALUES (?, ?, ?, ?)', (name, icon, desc, uid))
    ws_id = cursor.lastrowid
    conn.execute('INSERT INTO WorkspaceMembers (workspace_id, user_id, role) VALUES (?, ?, ?)', (ws_id, uid, 'Owner'))
    conn.commit()
    conn.close()
    log_activity(uid, "Created Workspace", f"Workspace: {name}")
    return jsonify({'success': True, 'id': ws_id})

@app.route('/api/workspace/delete/<int:ws_id>', methods=['POST'])
@login_required
def delete_workspace(ws_id):
    uid = session['user_id']
    conn = get_db()
    ws = conn.execute('SELECT * FROM Workspaces WHERE id = ? AND owner_id = ?', (ws_id, uid)).fetchone()
    if not ws: return jsonify({'error': 'Unauthorized'}), 403
    
    conn.execute('DELETE FROM Workspaces WHERE id = ?', (ws_id,))
    conn.execute('DELETE FROM WorkspaceMembers WHERE workspace_id = ?', (ws_id,))
    # Mark docs in this workspace as deleted or move to default? For now, we'll just leave them unassigned or delete.
    conn.execute('UPDATE Documents SET workspace_id = NULL WHERE workspace_id = ?', (ws_id,))
    conn.commit()
    conn.close()
    log_activity(uid, "Deleted Workspace", f"WS ID: {ws_id}")
    return jsonify({'success': True})

@app.route('/api/workspace/invite', methods=['POST'])
@login_required
def invite_user():
    data = request.json
    workspace_id = data.get('workspace_id')
    email = data.get('email')
    
    uid = session['user_id']
    conn = get_db()
    
    # Ownership Check
    ws = conn.execute('SELECT * FROM Workspaces WHERE id = ? AND owner_id = ?', (workspace_id, uid)).fetchone()
    if not ws: return jsonify({'error': 'Unauthorized workspace control'}), 403
    
    # Target User
    target = conn.execute('SELECT id FROM Users WHERE email = ?', (email,)).fetchone()
    if not target: return jsonify({'error': 'Intelligence practitioner not found'}), 404
    
    try:
        conn.execute('INSERT INTO WorkspaceMembers (workspace_id, user_id, role) VALUES (?, ?, ?)', (workspace_id, target['id'], 'Member'))
        conn.commit()
        log_activity(uid, "Collaboration Invite", f"User {email} added to {ws['name']}")
        return jsonify({'success': True})
    except: return jsonify({'error': 'Practitioner already in network'}), 400
    finally: conn.close()
@socketio.on('join')
def on_join(data):
    room = f"doc_{data['doc_id']}"
    join_room(room)
    uid = session.get('user_id')
    user = session.get('username', 'Anonymous')
    emit('presence', {'user_id': uid, 'username': user, 'status': 'online'}, room=room)

@socketio.on('edit')
def on_edit(data):
    room = f"doc_{data['doc_id']}"
    data['user_id'] = session.get('user_id')
    data['username'] = session.get('username', 'Anonymous')
    emit('edit', data, room=room, include_self=False)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
