import sys
import os
from dotenv import load_dotenv
from wherobots.db import connect

load_dotenv()
API_KEY = os.getenv("WHEROBOTS_API_KEY")

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("Connecting to Wherobots Spatial SQL API...")
    conn = connect(api_key=API_KEY)
    cursor = conn.cursor()
    
    # 1. Show databases
    cursor.execute("SHOW DATABASES IN org_catalog")
    df_db = cursor.fetchall()
    print("\n=== Databases ===")
    print(df_db)
    
    # 2. Show tables in org_catalog.fgsdb
    cursor.execute("SHOW TABLES IN org_catalog.fgsdb")
    df_tables = cursor.fetchall()
    print("\n=== Tables in org_catalog.fgsdb ===")
    print(df_tables)
    
    # 3. Query sub-precincts
    cursor.execute("SELECT * FROM org_catalog.fgsdb.precinct_sub_precincts")
    df_sub = cursor.fetchall()
    print("\n=== Sub-Precincts Table ===")
    print(df_sub)
    
    # 4. Query net developable zones (including area)
    cursor.execute("""
        SELECT precinct_key, 
               ST_Area(net_developable_geom) / 1e4 AS net_developable_ha 
        FROM org_catalog.fgsdb.precinct_net_developable_zones
    """)
    df_zones = cursor.fetchall()
    print("\n=== Net Developable Zones Area ===")
    print(df_zones)

if __name__ == "__main__":
    main()
