import sqlite3
import csv

conn = sqlite3.connect("store.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT,
    customer_name TEXT,
    email TEXT,
    item_id TEXT,
    item_name TEXT,
    price INTEGER,
    quantity INTEGER,
    total_amount INTEGER,
    transaction_type TEXT,
    date TEXT
)
""")

cursor.execute("DELETE FROM transactions")

with open("data/store_data.csv", newline="") as file:
    reader = csv.DictReader(file)
    for row in reader:
        cursor.execute("""
        INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            row["transaction_id"],
            row["customer_id"],
            row["customer_name"],
            row["email"],
            row["item_id"],
            row["item_name"],
            row["price"],
            row["quantity"],
            row["total_amount"],
            row["transaction_type"],
            row["date"]
        ))

conn.commit()
conn.close()
print("✅ Database initialized successfully")
