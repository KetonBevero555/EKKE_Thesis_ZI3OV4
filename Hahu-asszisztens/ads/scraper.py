import os
import sys
import django
import re
import time
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

# --- KONFIGURÁCIÓ ---
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hahu_backend.settings')
django.setup()

from ads.models import DummyAd, ScrapeLog

# --- OKOS ADATTISZTÍTÓK ---
def clean_price(text):
    if not text: return None
    clean_str = re.sub(r'[^\d]', '', text)
    return int(clean_str) if clean_str else None

def parse_tech_info(info_elements):
    data = {'fuel': None, 'year': None, 'month': None, 'engine_cc': None, 'power_le': None, 'power_kw': None, 'mileage': None}
    
    for item in info_elements:
        raw_text = item.strip().replace('\xa0', ' ')
        text_lower = raw_text.lower()
        
        if re.search(r'\d{4}/\d{1,2}', raw_text):
            parts = raw_text.split('/')
            data['year'] = int(re.sub(r'[^\d]', '', parts[0]))
            data['month'] = int(re.sub(r'[^\d]', '', parts[1]))
        elif re.match(r'^\d{4}$', raw_text.strip(',')):
            data['year'] = int(re.sub(r'[^\d]', '', raw_text))
        elif 'benzin' in text_lower and 'lpg' not in text_lower: data['fuel'] = 'Benzin'
        elif 'dízel' in text_lower or 'diesel' in text_lower: data['fuel'] = 'Dízel'
        elif 'elektromos' in text_lower: data['fuel'] = 'Elektromos'
        elif 'hibrid' in text_lower: data['fuel'] = 'Hibrid'
        elif 'lpg' in text_lower: data['fuel'] = 'LPG'
        elif 'cng' in text_lower: data['fuel'] = 'CNG'
        elif 'cm³' in raw_text:
            data['engine_cc'] = int(re.sub(r'[^\d]', '', raw_text))
        elif 'kW' in raw_text:
            data['power_kw'] = int(re.sub(r'[^\d]', '', raw_text.split('kW')[0]))
        elif 'LE' in raw_text:
            data['power_le'] = int(re.sub(r'[^\d]', '', raw_text.split('LE')[0]))
        elif 'km' in raw_text and 'km-re' not in text_lower:
            data['mileage'] = int(re.sub(r'[^\d]', '', raw_text))
            
    return data

# --- A FŐ SCRAPER ---
def run_scraper():
    print("--- SCRAPER INDÍTÁSA ---")
    
    # 1. ADATBÁZIS ÜRÍTÉSE
    print("DummyAd tábla ürítése...")
    count = DummyAd.objects.count()
    DummyAd.objects.all().delete()
    print(f"Törölve {count} régi hirdetés.")

    log = ScrapeLog.objects.create(expected_cars=0, status="INDULAS")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "chrome_profile")
    
    try:
        sb = sb_cdp.Chrome(user_data_dir=profile_dir, incognito=False)
        endpoint_url = sb.get_endpoint_url()
    except Exception as e:
        print(f"Hiba a böngésző indításakor: {e}")
        return

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(endpoint_url)
            context = browser.contexts[0]
            page = context.pages[0]

            print("Főoldal nyitása...")
            page.goto("https://www.hasznaltauto.hu/")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)

            # Captcha és Cookie kezelés
            sb.solve_captcha()
            try:
                cookie_btn = page.query_selector('text="Elfogadás és bezárás"')
                if cookie_btn and cookie_btn.is_visible():
                    cookie_btn.click()
                    time.sleep(1)
            except: pass

            # Keresés
            print("Keresés indítása...")
            search_btn = page.query_selector('[data-testid="submit-button"]')
            if search_btn:
                search_btn.click()
                time.sleep(5)
                sb.solve_captcha()
            else:
                print("Nem találtam a keresés gombot (lehet már listán vagyunk).")

            # --- LAPOZÓ CIKLUS ---
            page_num = 1
            total_saved = 0
            
            while True:
                print(f"\n--- {page_num}. OLDAL FELDOLGOZÁSA ---")
                
                # Várakozás a listára
                try:
                    page.wait_for_selector(".talalati-sor", timeout=15000)
                except:
                    print("Időtúllépés vagy üres oldal.")
                    break

                # Autók kigyűjtése az aktuális oldalról
                car_cards = page.query_selector_all(".talalati-sor")
                print(f"Autók ezen az oldalon: {len(car_cards)}")
                
                for card in car_cards:
                    try:
                        link_el = card.query_selector("h3 a")
                        if not link_el: continue
                        
                        full_url = link_el.get_attribute("href")
                        title = link_el.inner_text()
                        hahu_id = int(full_url.split('-')[-1])

                        # Márka/Modell
                        parts = full_url.split('/')
                        brand = "Egyéb"
                        model = ""
                        if 'szemelyauto' in parts:
                            idx = parts.index('szemelyauto')
                            if len(parts) > idx + 2:
                                brand = parts[idx+1].capitalize()
                                model = parts[idx+2].capitalize().replace('_', ' ')
                        elif 'kishaszonjarmu' in parts:
                             idx = parts.index('kishaszonjarmu')
                             if len(parts) > idx + 2:
                                brand = parts[idx+1].capitalize()
                                model = parts[idx+2].capitalize().replace('_', ' ')

                        # Árak
                        price_primary = card.query_selector(".pricefield-primary")
                        price_secondary = card.query_selector(".pricefield-secondary-basic")
                        p1 = clean_price(price_primary.inner_text()) if price_primary else None
                        p2 = clean_price(price_secondary.inner_text()) if price_secondary else None
                        final_price = p1
                        sale_price = p2 if p2 else None

                        # Tech info
                        info_spans = card.query_selector_all(".talalatisor-info.adatok span.info")
                        if not info_spans:
                             info_spans = card.query_selector_all(".talalatisor-info span.info")
                        tech = parse_tech_info([span.inner_text() for span in info_spans])

                        # Címkék (duplikáció mentesítve)
                        tag_spans = card.query_selector_all(".cimke-lista span.label")
                        unique_tags = sorted(list(set([t.inner_text() for t in tag_spans if t.inner_text().strip()])))
                        tags = "|".join(unique_tags)

                        # Leírás/Eladó
                        desc_el = card.query_selector(".talalati-sor__leiras")
                        description = desc_el.inner_text() if desc_el else ""
                        seller_el = card.query_selector(".trader-name")
                        seller = seller_el.inner_text().replace("Kereskedés: ", "") if seller_el else "Magánszemély"

                        DummyAd.objects.create(
                            hahu_id=hahu_id,
                            url=full_url,
                            title=title,
                            brand=brand,
                            model=model,
                            price=final_price,
                            sale_price=sale_price,
                            fuel=tech['fuel'],
                            year=tech['year'],
                            month=tech['month'],
                            engine_cc=tech['engine_cc'],
                            power_le=tech['power_le'],
                            power_kw=tech['power_kw'],
                            mileage=tech['mileage'],
                            tags=tags,
                            description_snippet=description,
                            seller=seller,
                            no_price=True if not final_price else False
                        )
                        total_saved += 1
                        
                    except Exception as e:
                        print(f"[SKIP] Hiba: {e}") # Opcionális: ha túl sok a zaj, kikommentelheted
                        continue

                print(f"[STATUS] Eddig mentve: {total_saved} autó.")
                
                # --- LAPOZÁS LOGIKA (A TE HTML KÓDOD ALAPJÁN) ---
                # Megkeressük a "li.next" elemet
                next_li = page.query_selector("li.next")
                
                if next_li:
                    # Megnézzük, hogy le van-e tiltva (van-e 'disabled' osztálya)
                    class_attr = next_li.get_attribute("class") or ""
                    
                    if "disabled" in class_attr:
                        print("Elértük az utolsó oldalt (Gomb letiltva).")
                        break
                    else:
                        # Ha nincs letiltva, megkeressük benne a linket és kattintunk
                        next_link = next_li.query_selector("a")
                        if next_link:
                            print(f"Kattintás a következő oldalra ({page_num + 1})...")
                            next_link.click()
                            page_num += 1
                            
                            # Várakozás a lapozás után
                            time.sleep(3) 
                            sb.solve_captcha() # Biztonsági ellenőrzés lapozás után
                        else:
                            print("Hiba: Van 'next' gomb, de nincs benne link.")
                            break
                else:
                    print("Nincs 'Következő' gomb az oldalon. Vége.")
                    break

            log.status = "SIKERES"
            log.actual_scraped = total_saved
            log.save()
            print("------------------------------------------------")
            print(f"KÉSZ! Összesen {total_saved} autó lementve {page_num} oldalról.")
            print("------------------------------------------------")

        except Exception as e:
            print(f"Kritikus hiba: {e}")
            log.status = f"CRITICAL: {str(e)}"
            log.save()
        finally:
            print("Böngésző bezárása...")
            try:
                browser.close()
            except: pass

if __name__ == "__main__":
    run_scraper()
