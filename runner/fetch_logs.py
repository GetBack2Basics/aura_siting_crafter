import os
import sys
from dotenv import load_dotenv
from wherobots import WherobotsJob

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_logs.py <run_id>")
        return
    run_id = sys.argv[1]
    job = WherobotsJob.from_run_id(run_id, api_key=os.getenv("WHEROBOTS_API_KEY"))
    cursor = 0
    while True:
        logs = job.get_logs(cursor=cursor, size=100)
        for item in logs.items:
            print(item.raw)
        cursor = logs.next_page
        if not cursor:
            break

if __name__ == "__main__":
    main()
