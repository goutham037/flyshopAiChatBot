import asyncio
from app.db.database import execute_readonly_query

async def main():
    try:
        rows = await execute_readonly_query("SELECT count(*) as c FROM query_activity_markups", {})
        count = rows[0]['c']
        print(f"TOTAL MARKUPS: {count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
