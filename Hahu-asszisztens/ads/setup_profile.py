import os
import sys
import time
import shutil
import django
import re
from django.utils import timezone
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

# Konfiguráció
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hahu_backend.settings')
django.setup()

# Böngészőben dolgozza fel a cookie-kat, captcha-t, és egyéb akadályokat, hogy a profil készen álljon a scraper indítására
def run_setup() -> None:
    print("--- STARTING SCRAPER SETUP ---")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "chrome_profile")
    
    if os.path.exists(profile_dir):
        print(f"[*] Deleting old profile: {profile_dir}...")
        try:
            shutil.rmtree(profile_dir)
            print("[*] Old profile deleted successfully!")
        except Exception as e:
            print(f"[!] Error occurred while deleting the profile: {e}")
            raise Exception("Failed to delete the old profile.")

    if not os.path.exists(profile_dir):
        print(f"[*] Creating new profile folder here: {profile_dir}")

    try:
        sb = sb_cdp.Chrome(user_data_dir=profile_dir, incognito=False, headless=False)
        endpoint = sb.get_endpoint_url()
        print(f"<S> Browser is running. Endpoint: {endpoint}")
    except Exception as e:
        print(f"[!] Error starting browser: {e}")
        raise Exception("Failed to start the browser.")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        context = browser.contexts[0]
        page = context.pages[0]

        print("<S> Starting the homepage...")
        page.goto("https://www.hasznaltauto.hu/")

        print("<S> Waiting/Captcha verification...")
        time.sleep(5) # Várakozás a teljes betöltődésre
        sb.solve_captcha()

        print("<S> Searching for cookie panel...")
        cookie_accepted = False
        for _ in range(10):
            try:
                agree_btn = page.query_selector("#didomi-notice-agree-button")
                if agree_btn and agree_btn.is_visible():
                    agree_btn.click(force=True)
                    print("<S> Cookies accepted successfully!")
                    cookie_accepted = True
                    break
            except:
                pass
            time.sleep(2)
        
        if not cookie_accepted:
            print("<S> Cookie panel not found!")

        search_btn = page.wait_for_selector('[data-testid="submit-button"]', state="visible", timeout=45000)
        print("<S> Clicking the 'Search' button...")
        if search_btn:
            search_btn.click()
            
            if not page.wait_for_selector(".talalati-sor", timeout=60000):
                raise Exception("Search results failed to load!")
                
            print("<S> Search results loaded. Profile configured!")
        else:
            raise Exception("Search button missing!")
        
        print("<S> Closing the browser...")
        time.sleep(3) # Várakozás a bezárás előtt
        try:
            browser.close() # Playwright böngésző bezárása
            sb.driver.quit() # SeleniumBase driver bezárása (Ha a Playwright nem zárta volna be az oldalt)
        except Exception as e:
            print(f"[!] Error closing the browser: {e}")
            raise Exception("Failed to close the setup browser properly.")

if __name__ == "__main__":
    run_setup()
