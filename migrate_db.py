import sqlite3

def run_migration():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check Users table columns
    cursor.execute('PRAGMA table_info(Users)')
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current Users columns: {columns}")
    
    # Fix Users table
    if 'name' in columns and 'username' not in columns:
        print("Renaming 'name' to 'username' in Users table...")
        cursor.execute('ALTER TABLE Users RENAME COLUMN name TO username')
    
    if 'bio' not in columns:
        print("Adding 'bio' column to Users table...")
        cursor.execute('ALTER TABLE Users ADD COLUMN bio TEXT')
    
    # Check other tables if they exist and have correct columns as per app.py
    # Workspaces
    cursor.execute('PRAGMA table_info(Workspaces)')
    ws_cols = [col[1] for col in cursor.fetchall()]
    if ws_cols:
        if 'icon' not in ws_cols:
            print("Adding 'icon' column to Workspaces table...")
            cursor.execute('ALTER TABLE Workspaces ADD COLUMN icon TEXT DEFAULT "📁"')
        if 'description' not in ws_cols:
            print("Adding 'description' column to Workspaces table...")
            cursor.execute('ALTER TABLE Workspaces ADD COLUMN description TEXT')
            
    # Documents
    cursor.execute('PRAGMA table_info(Documents)')
    doc_cols = [col[1] for col in cursor.fetchall()]
    if doc_cols:
        if 'workspace_id' not in doc_cols:
            print("Adding 'workspace_id' column to Documents table...")
            cursor.execute('ALTER TABLE Documents ADD COLUMN workspace_id INTEGER')
        if 'is_deleted' not in doc_cols:
            print("Adding 'is_deleted' column to Documents table...")
            cursor.execute('ALTER TABLE Documents ADD COLUMN is_deleted INTEGER DEFAULT 0')

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == '__main__':
    run_migration()
