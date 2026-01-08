
import os
import time
from dotenv import load_dotenv
from register_automation_playwright import RegisterDNSUpdater

def test_login():
    print("starting automated test...")
    load_dotenv()
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    DOMAIN = os.getenv('DOMINIO') or "example.com" # fallback or error check
    
    import requests
    try:
        current_ip = requests.get('https://api.ipify.org').text
        print(f"Test Public IP: {current_ip}")
    except:
        current_ip = "127.0.0.1"

    # Headless=False for debugging visibility
    updater = RegisterDNSUpdater(EMAIL, PASSWORD, domain=DOMAIN, headless=False)
    
    try:
        print("Starting Update IP Test...")
        # Verify full flow: Login -> Navigate -> Update (or Skip) -> Logout/Close
        success = updater.update_ip(current_ip)
        
        if success:
            print("AUTOMATED_TEST: UPDATE_SUCCESS")
        else:
            print("AUTOMATED_TEST: UPDATE_FAILURE")
            
    except Exception as e:
        print(f"AUTOMATED_TEST: ERROR - {e}")
    finally:
        updater.close()

if __name__ == "__main__":
    test_login()
