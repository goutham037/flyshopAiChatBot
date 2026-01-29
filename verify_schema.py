import asyncio
from sqlalchemy import text
from app.db.database import get_db_session

async def check_schema():
    query = "SELECT * FROM master_admins WHERE id = 18"
    async with get_db_session() as session:
        result = await session.execute(text(query))
        row = result.fetchone()
        if row:
            columns = result.keys()
            row_dict = dict(zip(columns, row))
            print(f"\nRow 18 data: {row_dict}")
        else:
            print("\nRow 18 not found")

if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # Load .env manually
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

    asyncio.run(check_schema())
