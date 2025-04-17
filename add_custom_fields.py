from app import db, create_app
import sqlite3

app = create_app()

# Update this path to match your SQLite database location
DB_PATH = 'instance/trkaljka.db'  # Common location for Flask SQLite databases

with app.app_context():
    # Use SQLite's ALTER TABLE to add the column
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists to prevent errors
        cursor.execute("PRAGMA table_info(race_result)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'custom_fields' not in columns:
            print("Adding custom_fields column to race_result table...")
            cursor.execute("ALTER TABLE race_result ADD COLUMN custom_fields TEXT")
            conn.commit()
            print("Column added successfully!")
        else:
            print("custom_fields column already exists!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()