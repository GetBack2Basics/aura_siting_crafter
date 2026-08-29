import sys
import os
from dotenv import load_dotenv
from wherobots import WherobotsJob

load_dotenv()
API_KEY = os.getenv("WHEROBOTS_API_KEY")

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    runs = WherobotsJob.list_runs(api_key=API_KEY, size=1)
    if runs.items:
        r = runs.items[0]
        print("RunView class:", type(r))
        print("Attributes:", dir(r))
        try:
            print("Dict representation:", r.__dict__)
        except:
            pass

if __name__ == "__main__":
    main()
