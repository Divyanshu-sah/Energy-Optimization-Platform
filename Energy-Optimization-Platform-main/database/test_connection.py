"""
Test PostgreSQL connection from Python
Run this first to verify everything works
"""

import psycopg2

# Update these with YOUR credentials from pgAdmin
DB_CONFIG = {
    'host': 'localhost',      # From pgAdmin properties
    'port': 5432,             # Default PostgreSQL port
    'user': 'postgres',       # Your username
    'password': 'postgres',   # Your password (what you set during install)
    'database': 'postgres'    # Connect to default database first
}

def test_connection():
    """Test if Python can connect to PostgreSQL"""
    print("🔌 Testing PostgreSQL connection...")
    
    try:
        # Try to connect
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Successfully connected to PostgreSQL!")
        
        # Get PostgreSQL version
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"📦 PostgreSQL Version: {version[:50]}...")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n✅ Connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Is PostgreSQL running?")
        print("2. Are credentials correct?")
        print("3. Check pgAdmin for correct host/port")
        return False

def list_databases():
    """List all databases"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        
        print("\n📊 Available databases:")
        for db in databases:
            print(f"  - {db[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error listing databases: {e}")

if __name__ == "__main__":
    if test_connection():
        list_databases()