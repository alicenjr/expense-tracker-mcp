from fastmcp import FastMCP
import os
import sqlite3

db_path=os.path.join(os.path.dirname(__file__), "database.db")
mcp = FastMCP("expenseTracker")

def init_db():
    with sqlite3.connect(db_path) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT DEFAULT '',
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            note TEXT DEFAULT ''
        )
        """)
init_db()

@mcp.tool()
def add_expense(date, amount, description, category, subcategory="", note=""):
    with sqlite3.connect(db_path) as c:
        cur = c.execute(
            "INSERT INTO expenses (description, category, subcategory, amount, date, note) VALUES (?, ?, ?, ?, ?, ?)",
            (description, category, subcategory, amount, date, note)
        )
        return {'status':'ok','id': cur.lastrowid}

@mcp.tool()
def list_expenses():
    with sqlite3.connect(db_path) as c:
        cur = c.execute("SELECT * FROM expenses")
        cols = [description[0] for description in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

if __name__ == "__main__":
    mcp.run()