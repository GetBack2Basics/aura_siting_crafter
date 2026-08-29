import os
import sys
from dotenv import load_dotenv
from wherobots import WherobotsJob

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')
API_KEY = os.getenv("WHEROBOTS_API_KEY")

def run_job(script_path, name):
    print(f"\n==========================================")
    print(f"Submitting {name} job to Wherobots...")
    print(f"==========================================")
    
    # Declare config dependency
    config_dep = WherobotsJob.add_file_dependency("config/national.json")
    
    # Initialize job
    job = WherobotsJob(
        script=script_path,
        name=name,
        runtime="tiny",
        api_key=API_KEY,
        dependencies=[config_dep],
    )
    
    # Submit job
    job.submit()
    print(f"Job submitted successfully. Run ID: {job.run_id}")
    
    # Wait for completion and stream logs
    print("Waiting for job completion...")
    status = job.wait_for_completion(stream_logs=True)
    print(f"Job finished with status: {status}")
    return status

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "datacenter":
        run_job("src/Analysis/datacenter_suitability.py", "aura-datacenter-analysis")
    elif len(sys.argv) > 1 and sys.argv[1] == "national":
        run_job("src/Analysis/national_suitability_analysis.py", "aura-national-analysis")
    else:
        status1 = run_job("src/Analysis/datacenter_suitability.py", "aura-datacenter-analysis")
        status2 = run_job("src/Analysis/national_suitability_analysis.py", "aura-national-analysis")
        if status1.value != "COMPLETED" or status2.value != "COMPLETED":
            sys.exit(1)

if __name__ == "__main__":
    main()
