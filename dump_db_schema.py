
import asyncio
import aiomysql
import json
from datetime import datetime, date
from decimal import Decimal

DB_CONFIG = {
    "host": "82.25.121.78",
    "port": 3306,
    "user": "u271850780_crm",
    "password": "=l7OsdtiqUC",
    "db": "u271850780_crm_api",
    "connect_timeout": 10
}

def serialize_value(val):
    """Convert non-JSON-serializable types to strings."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    elif isinstance(val, Decimal):
        return float(val)
    elif isinstance(val, bytes):
        return val.decode('utf-8', errors='replace')
    elif hasattr(val, 'total_seconds'):  # timedelta
        return str(val)
    return val

async def dump_database():
    print("Connecting to database...")
    conn = await aiomysql.connect(**DB_CONFIG)
    
    result = {}
    
    async with conn.cursor() as cursor:
        # Get all tables
        await cursor.execute("SHOW TABLES")
        tables = await cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        print(f"\nFound {len(table_names)} tables:")
        for name in table_names:
            print(f"  - {name}")
        
        result["_meta"] = {
            "database": DB_CONFIG["db"],
            "tables_count": len(table_names),
            "extracted_at": datetime.now().isoformat()
        }
        
        # Get first 10 rows from each table
        for table in table_names:
            print(f"\nFetching from {table}...")
            
            # Get column names
            await cursor.execute(f"DESCRIBE `{table}`")
            columns_info = await cursor.fetchall()
            columns = [col[0] for col in columns_info]
            
            # Get row count
            await cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = (await cursor.fetchone())[0]
            
            # Get first 10 rows
            await cursor.execute(f"SELECT * FROM `{table}` LIMIT 10")
            rows = await cursor.fetchall()
            
            # Convert to list of dicts
            rows_data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = serialize_value(row[i])
                rows_data.append(row_dict)
            
            result[table] = {
                "columns": columns,
                "total_rows": count,
                "sample_rows": rows_data
            }
            
            print(f"  Columns: {columns[:5]}{'...' if len(columns) > 5 else ''}")
            print(f"  Total rows: {count}, Fetched: {len(rows_data)}")
    
    conn.close()
    
    # Save to file
    output_file = "db_schema_and_samples.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Data saved to {output_file}")
    return result

if __name__ == "__main__":
    asyncio.run(dump_database())
