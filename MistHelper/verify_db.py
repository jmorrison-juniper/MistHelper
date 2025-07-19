#!/usr/bin/env python3
"""Script to verify the SQLite database contains actual data"""

import sqlite3
import os

db_path = './data/mist_data.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Database {db_path} contains {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}")
        print(f"    Records: {count}")
        
        # Show sample data for SiteList table
        if table_name == 'SiteList':
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"    Sample data (first 3 records):")
            for i, row in enumerate(rows):
                print(f"      Record {i+1}:")
                for j, col_name in enumerate(columns):
                    if j < len(row):
                        value = row[j]
                        if len(str(value)) > 50:  # Truncate long values
                            value = str(value)[:50] + "..."
                        print(f"        {col_name}: {value}")
                print()
    
    conn.close()
else:
    print(f"Database {db_path} does not exist")
