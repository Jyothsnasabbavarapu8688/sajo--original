import sqlite3

def run_fix():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. Fix Users table
    cursor.execute('PRAGMA table_info(Users)')
    users_cols = [col[1] for col in cursor.fetchall()]
    if 'name' in users_cols and 'username' not in users_cols:
        print("Migrating Users table: name -> username...")
        cursor.execute('ALTER TABLE Users RENAME COLUMN name TO username')
    if 'bio' not in users_cols:
        print("Migrating Users table: +bio...")
        cursor.execute('ALTER TABLE Users ADD COLUMN bio TEXT')

    # 2. Fix Workspaces table
    cursor.execute('PRAGMA table_info(Workspaces)')
    ws_cols = [col[1] for col in cursor.fetchall()]
    if 'user_id' in ws_cols and 'owner_id' not in ws_cols:
        print("Migrating Workspaces table: user_id -> owner_id...")
        cursor.execute('ALTER TABLE Workspaces RENAME COLUMN user_id TO owner_id')
    if 'icon' not in ws_cols:
        print("Migrating Workspaces table: +icon...")
        cursor.execute('ALTER TABLE Workspaces ADD COLUMN icon TEXT DEFAULT "📁"')
    if 'description' not in ws_cols:
        print("Migrating Workspaces table: +description...")
        cursor.execute('ALTER TABLE Workspaces ADD COLUMN description TEXT')

    # 3. Fix Documents table
    cursor.execute('PRAGMA table_info(Documents)')
    doc_cols = [col[1] for col in cursor.fetchall()]
    if 'summary' not in doc_cols:
        print("Migrating Documents table: +summary...")
        cursor.execute('ALTER TABLE Documents ADD COLUMN summary TEXT')
    if 'bullets' not in doc_cols:
        print("Migrating Documents table: +bullets...")
        cursor.execute('ALTER TABLE Documents ADD COLUMN bullets TEXT')
    if 'tags' not in doc_cols:
        # It had tags, check file_type vs workspace_id
        pass
    if 'workspace_id' not in doc_cols:
        print("Migrating Documents table: +workspace_id...")
        cursor.execute('ALTER TABLE Documents ADD COLUMN workspace_id INTEGER')
    if 'is_deleted' not in doc_cols:
        print("Migrating Documents table: +is_deleted...")
        cursor.execute('ALTER TABLE Documents ADD COLUMN is_deleted INTEGER DEFAULT 0')
    if 'updated_at' not in doc_cols:
        print("Migrating Documents table: +updated_at...")
        cursor.execute('ALTER TABLE Documents ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

    # 4. Fix KnowledgeGraph table
    cursor.execute('PRAGMA table_info(KnowledgeGraph)')
    kg_cols = [col[1] for col in cursor.fetchall()]
    # Since KnowledgeGraph was found empty, we can just drop and recreate it perfectly.
    cursor.execute('SELECT COUNT(*) FROM KnowledgeGraph')
    if cursor.fetchone()[0] == 0:
        print("Recreating KnowledgeGraph table...")
        cursor.execute('DROP TABLE KnowledgeGraph')
        cursor.execute('''
        CREATE TABLE KnowledgeGraph (
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
    else:
        # Manual migration if not empty
        if 'document_id' in kg_cols and 'source_doc_id' not in kg_cols:
             cursor.execute('ALTER TABLE KnowledgeGraph RENAME COLUMN document_id TO source_doc_id')
        if 'concept_a' in kg_cols and 'concept' not in kg_cols:
             cursor.execute('ALTER TABLE KnowledgeGraph RENAME COLUMN concept_a TO concept')
        if 'concept_b' in kg_cols and 'linked_doc_id' not in kg_cols:
             cursor.execute('ALTER TABLE KnowledgeGraph RENAME COLUMN concept_b TO linked_doc_id') # Might be text instead of id though

    conn.commit()
    conn.close()
    print("Database schema fixed successfully.")

if __name__ == '__main__':
    run_fix()
