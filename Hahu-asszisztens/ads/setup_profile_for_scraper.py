import os
import time
import shutil
from seleniumbase import sb_cdp
from playwright.sync_api import sync_playwright

def setup_profile():
    # Profil mappa útvonalazsa
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "chrome_profile")
    
    # Ha van profil - töröljük
    if os.path.exists(profile_dir):
        print(f"[*] Régi profil törlése: {profile_dir}...")
        try:
            shutil.rmtree(profile_dir)
            print("[*] Régi profil sikeresen törölve!")
        except Exception as e:
            print(f"[*] Hiba a törlésnél: {e}")
            return
    
    print(f"[*] Új profil mappa létrehozása itt: {profile_dir}")

    # Böngésző indítása
    sb = sb_cdp.Chrome(
        user_data_dir=profile_dir,
        incognito=False,
        headless=True
    )
    endpoint = sb.get_endpoint_url()
    print(f"<P> Böngésző fut. Endpoint: {endpoint}")

    # Profil beállítása
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(endpoint)
            context = browser.contexts[0]
            page = context.pages[0]

            print("<P> Kezdőlap megnyitása...")
            page.goto("https://www.hasznaltauto.hu/")
            
            # Captcha megoldás (ha van)
            print("<P> Várakozás/Captcha ellenőrzése...")
            sb.solve_captcha()

            # Süti (Cookie) elfogadása
            print("<P> Süti panel keresése...")
            cookie_accepted = False
            for _ in range(10):
                try:
                    agree_btn = page.query_selector("#didomi-notice-agree-button")
                    if agree_btn and agree_btn.is_visible():
                        agree_btn.click(force=True)
                        print("<P> Sütik sikeresen elfogadva!")
                        cookie_accepted = True
                        break
                except:
                    pass
                time.sleep(1)
            
            if not cookie_accepted:
                print("<P> Süti panel nem található!")

            # Keresés gomb megnyomása a kezdőlapon
            print("<P> Kattintás a 'Keresés' gombra...")
            search_btn = page.query_selector('[data-testid="submit-button"]')
            if search_btn:
                search_btn.click()
                page.wait_for_selector(".talalati-sor", timeout=15000)
                print("<P> Találati lista betöltött.\nProfil beállítva!")
            
        except Exception as e:
            print(f"<P> Hiba a profil beállítása közben: {e}")
        finally:
            print("<P> Böngésző bezárása másodpercek múlva...")
            time.sleep(3)
            try:
                browser.close()
            except:
                pass

if __name__ == "__main__":
    setup_profile()
