import sqlite3

conn = sqlite3.connect('feedback.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM feedback")
rows = cursor.fetchall()

print("📄 All Feedback Entries:")
for row in rows:
    print(row)

conn.close()
