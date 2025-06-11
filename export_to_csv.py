import sqlite3
import csv

conn = sqlite3.connect('feedback.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM feedback")
rows = cursor.fetchall()

with open("feedback_export.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Text", "Sentiment"])
    writer.writerows(rows)

print("✅ Exported to feedback_export.csv")

conn.close()
