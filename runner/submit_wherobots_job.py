import os
import sys
from dotenv import load_dotenv
from wherobots import WherobotsJob

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')
API_KEY = os.getenv("WHEROBOTS_API_KEY")

def main():
    print("Initializing Wherobots Job submission...")
    
    # Declare dependencies
    config_dep = WherobotsJob.add_file_dependency("config/national.json")
    requests_dep = WherobotsJob.add_pypi_dependency("requests", "2.31.0")
    
    # Initialize job
    job = WherobotsJob(
        script="src/Ingestion/spatial_ingest.py",
        name="aura-spatial-etl",
        runtime="tiny",
        api_key=API_KEY,
        dependencies=[config_dep, requests_dep],
    )
    
    # Submit job
    print("Submitting job to Wherobots...")
    job.submit()
    print(f"Job submitted successfully. Run ID: {job.run_id}")
    
    # Wait for completion and stream logs
    print("Waiting for job completion...")
    status = job.wait_for_completion(stream_logs=True)
    print(f"Job finished with status: {status}")

if __name__ == "__main__":
    main()
