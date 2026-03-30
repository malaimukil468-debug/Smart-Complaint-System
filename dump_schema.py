import sqlite3
import json

db = sqlite3.connect('database.db')
schema = db.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
with open('c:/Users/malai/Desktop/Smart_Complaint_System/schema.txt', 'w') as f:
    for row in schema:
        if row[0]:
            f.write(row[0] + "\n")
