import sqlite3

DB_PATH = 'database.db'

def setup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Workspaces
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Workspaces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '📁',
        description TEXT,
        owner_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES Users (id)
    )
    ''')

    # Workspace Members
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS WorkspaceMembers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER,
        user_id INTEGER,
        role TEXT DEFAULT 'Member',
        FOREIGN KEY (workspace_id) REFERENCES Workspaces (id),
        FOREIGN KEY (user_id) REFERENCES Users (id)
    )
    ''')

    # Documents
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        summary TEXT,
        bullets TEXT,
        tags TEXT,
        user_id INTEGER,
        workspace_id INTEGER,
        is_deleted INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (id),
        FOREIGN KEY (workspace_id) REFERENCES Workspaces (id)
    )
    ''')

    # Document Versions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DocumentVersions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        content TEXT,
        version_num INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES Documents (id)
    )
    ''')

    # Knowledge Graph
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS KnowledgeGraph (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_doc_id INTEGER,
        concept TEXT,
        relationship TEXT,
        linked_doc_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_doc_id) REFERENCES Documents (id),
        FOREIGN KEY (linked_doc_id) REFERENCES Documents (id)
    )
    ''')

    # Activity Logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ActivityLogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database infrastructure initialized successfully.")

if __name__ == '__main__':
    setup()
