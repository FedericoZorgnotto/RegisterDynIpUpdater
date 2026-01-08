
import os
import sys
from dotenv import load_dotenv
from register_automation import RegisterDNSUpdater

def test_login():
    print("Starting Login Test (Automated)...")
    load_dotenv()
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    
    if not EMAIL or not PASSWORD:
        print("Error: EMAIL or PASSWORD not found in .env")
        return

    # User asked to run it "automatically", assuming headless or visible if possible.
    # We will try headless=False as user said manual interaction worked there.
    # But run_command might be headless context. Let's try headless=True first in code, 
    # but the class logic we updated defaults to whatever we pass.
    # Note: undetected-chromedriver forces use_subprocess=True which might help.
    
    updater = RegisterDNSUpdater(EMAIL, PASSWORD, headless=False)
    try:
        success = updater.login()
        if success:
            print("TEST RESULT: SUCCESS")
        else:
            print("TEST RESULT: FAILURE")
    except Exception as e:
        print(f"TEST RESULT: ERROR - {e}")
    finally:
        updater.close()

if __name__ == "__main__":
    test_login()
