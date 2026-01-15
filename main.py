from fastmcp import FastMCP
import os
import aiosqlite
import tempfile
import asyncio
import json

# ------------------------
# Paths
# ------------------------
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Database path: {DB_PATH}")

mcp = FastMCP("ExpenseTracker")

# ------------------------
# Async DB initialization
# ------------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        await db.commit()
        print("Database initialized successfully")

# ------------------------
# Tools
# ------------------------
@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        await db.commit()
        return {
            "status": "success",
            "id": cur.lastrowid
        }

@mcp.tool()
async def list_expenses(start_date, end_date):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, id DESC
        """, (start_date, end_date))

        cols = [c[0] for c in cur.description]
        rows = await cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY total_amount DESC"

        cur = await db.execute(query, params)
        cols = [c[0] for c in cur.description]
        rows = await cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]

# ------------------------
# Resource (FIXED)
# ------------------------
def _read_categories_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("expense:///categories", mime_type="application/json")
async def categories():
    if os.path.exists(CATEGORIES_PATH):
        return await asyncio.to_thread(_read_categories_file, CATEGORIES_PATH)

    return json.dumps({
        "categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Business",
            "Other"
        ]
    }, indent=2)

# ------------------------
# Server startup
# ------------------------
async def main():
    await init_db()
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8080
    )

if __name__ == "__main__":
    asyncio.run(main())
