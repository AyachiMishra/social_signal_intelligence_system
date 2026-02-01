import subprocess
import time
import sys

def run_pipeline():
    """Executes the analysis and transfer scripts in order."""
    try:
        print("\n" + "="*40)
        print(f"PIPELINE START: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Run the AI Intelligence Script
        print("Step 1: Running adan_intelligence.py...")
        subprocess.run([sys.executable, "adan_intelligence.py"], check=True)
        
        # 2. Run the Signal Transfer Script
        print("Step 2: Running signal_transfer.py...")
        subprocess.run([sys.executable, "signal_transfer.py"], check=True)
        
        print("PIPELINE COMPLETE: Data merged and temporary files wiped.")
        print("="*40)

    except subprocess.CalledProcessError as e:
        print(f"CRITICAL ERROR: A script failed to execute. {e}")
    except Exception as e:
        print(f"AN UNEXPECTED ERROR OCCURRED: {e}")

if __name__ == "__main__":
    # SET YOUR INTERVAL HERE (e.g., 30 seconds)
    INTERVAL_SECONDS = 30 
    
    print(f"ADAN Bank Automation Active. Running every {INTERVAL_SECONDS}s.")
    print("Press CTRL+C to stop the automation safely.")

    try:
        while True:
            run_pipeline()
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nAutomation stopped by user. Cleaning up...")