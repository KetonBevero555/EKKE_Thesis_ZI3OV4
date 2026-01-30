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

from ads.models import DummyAd, Ad, ScrapeLog

# --- SZÍNEK ---
class Colors:
    YELLOW = '\033[93m'
    RESET = '\033[0m'

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
    print("--- SCRAPER INDÍTÁSA (STABILIZÁLT VERZIÓ) ---")
    
    print("Ideiglenes tábla (DummyAd) ürítése...")
    DummyAd.objects.all().delete()

    log = ScrapeLog.objects.create(expected_cars=0, status="FUT")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "chrome_profile")
    
    try:
        sb = sb_cdp.Chrome(user_data_dir=profile_dir, incognito=False)
        endpoint_url = sb.get_endpoint_url()
    except Exception as e:
        print(f"Hiba a böngésző indításakor: {e}")
        return

    success = False
    total_saved = 0 

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(endpoint_url)
            context = browser.contexts[0]
            page = context.pages[0]

            # --- AdBlock ---
            print("Képblokkoló aktiválása...")
            def route_intercept(route):
                if route.request.resource_type in ["image", "media"]:
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", route_intercept)

            print("Főoldal nyitása...")
            page.goto("https://www.hasznaltauto.hu/")
            try: page.wait_for_load_state("domcontentloaded")
            except: pass
            time.sleep(2)
            sb.solve_captcha()

            print("Keresés indítása...")
            search_btn = page.query_selector('[data-testid="submit-button"]')
            if search_btn:
                search_btn.click()
                print("Várakozás a találati listára...")
                try:
                    # Itt hagytam a nagy timeoutot az első betöltéshez
                    page.wait_for_selector(".talalati-sor", timeout=45000)
                except:
                    print("Lassú első betöltés...")
                sb.solve_captcha()
            else:
                print("HIBA: Nincs keresés gomb, ugrás direkt linkre...")
                page.goto("https://www.hasznaltauto.hu/talalatilista/")

            # --- LAPOZÓ CIKLUS ---
            page_num = 1
            
            while True:
                print(f"\n--- {page_num}. OLDAL FELDOLGOZÁSA ---")
                
                # --- ÚJ: RETRY LOGIKA ---
                # Nem lépünk ki azonnal, ha timeout van, hanem próbálkozunk 3-szor
                page_loaded = False
                for attempt in range(1, 4): # 1, 2, 3 próbálkozás
                    try:
                        # ITT VOLT A HIBA: Felvittem 45 másodpercre a timeoutot!
                        page.wait_for_selector(".talalati-sor", timeout=45000)
                        page_loaded = True
                        break # Ha sikerült, kilépünk a próbálkozós ciklusból
                    except:
                        print(f"⚠️  Lassú válasz... Újrapróbálkozás ({attempt}/3)...")
                        time.sleep(3) # Kis pihenő
                
                if not page_loaded:
                    print("❌ VÉGLEGES TIMEOUT. A Hahu nem válaszol 3 próba után sem.")
                    log.status = f"TIMEOUT_ON_PAGE_{page_num}"
                    log.save()
                    break # Itt adjuk fel végleg

                # Innentől minden változatlan...
                car_cards = page.query_selector_all(".talalati-sor")
                count_on_page = len(car_cards)
                print(f"[INFO] Találatok az oldalon: {count_on_page} db")
                
                new_on_page = 0
                updated_on_page = 0
                
                for card in car_cards:
                    try:
                        link_el = card.query_selector("h3 a")
                        if not link_el: continue
                        
                        full_url = link_el.get_attribute("href")
                        title = link_el.inner_text()
                        hahu_id = int(full_url.split('-')[-1])

                        parts = full_url.split('/')
                        brand = "Egyéb"; model = ""
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

                        price_primary = card.query_selector(".pricefield-primary")
                        price_secondary = card.query_selector(".pricefield-secondary-basic")
                        raw_p1 = price_primary.inner_text() if price_primary else ""
                        raw_p2 = price_secondary.inner_text() if price_secondary else ""
                        is_rentable = "bérelhető" in raw_p1.lower() or "bérelhető" in raw_p2.lower()
                        p1 = clean_price(raw_p1); p2 = clean_price(raw_p2)
                        final_price = p1
                        sale_price = p2 if p2 else None

                        info_spans = card.query_selector_all(".talalatisor-info.adatok span.info")
                        if not info_spans: info_spans = card.query_selector_all(".talalatisor-info span.info")
                        tech = parse_tech_info([span.inner_text() for span in info_spans])

                        tag_spans = card.query_selector_all(".cimke-lista span.label")
                        unique_tags = sorted(list(set([t.inner_text() for t in tag_spans if t.inner_text().strip()])))
                        tags = "|".join(unique_tags)

                        desc_el = card.query_selector(".talalati-sor__leiras")
                        description = desc_el.inner_text() if desc_el else ""
                        seller_el = card.query_selector(".trader-name")
                        seller = seller_el.inner_text().replace("Kereskedés: ", "") if seller_el else "Magánszemély"

                        obj, created = DummyAd.objects.update_or_create(
                            hahu_id=hahu_id,
                            defaults={
                                'url': full_url, 'title': title, 'brand': brand, 'model': model,
                                'price': final_price, 'sale_price': sale_price, 'is_rentable': is_rentable,
                                'fuel': tech['fuel'], 'year': tech['year'], 'month': tech['month'],
                                'engine_cc': tech['engine_cc'], 'power_le': tech['power_le'], 'power_kw': tech['power_kw'],
                                'mileage': tech['mileage'], 'tags': tags, 'description_snippet': description,
                                'seller': seller, 'no_price': True if not final_price else False
                            }
                        )
                        
                        if created: new_on_page += 1
                        else: updated_on_page += 1
                        total_saved += 1
                        
                    except Exception:
                        continue

                print(f"[SAVE] Mentett hirdetések: {new_on_page} db")
                
                if updated_on_page > 0:
                    print(f"{Colors.YELLOW}[UPDATE] Frissített hirdetések: {updated_on_page} db{Colors.RESET}")
                
                print(f"[STATUS] Eddig mentve: {total_saved} autó.")

                # Lapozás
                next_li = page.query_selector("li.next")
                if next_li:
                    if "disabled" in (next_li.get_attribute("class") or ""):
                        print("Elértük az utolsó oldalt.")
                        success = True 
                        break
                    else:
                        next_link = next_li.query_selector("a")
                        if next_link:
                            print(f"Lapozás a következő oldalra ({page_num + 1})...")
                            next_link.click()
                            page_num += 1
                            time.sleep(2) 
                            sb.solve_captcha()
                        else:
                            success = True
                            break
                else:
                    success = True
                    break
                
                print("-----------------------------------")

        except Exception as e:
            print(f"KRITIKUS HIBA: {e}")
            log.status = f"CRITICAL_ERROR: {str(e)}"
            success = False
        finally:
            print("Böngésző bezárása...")
            try: browser.close()
            except: pass

    # --- MÁSOLÁS ---
    print("\n================================================")
    if success and total_saved > 0:
        print("✅ SIKERES FUTÁS! Adatok átmásolása az ÉLES táblába...")
        try:
            Ad.objects.all().delete()
            dummy_data = DummyAd.objects.values().exclude(id__isnull=True)
            new_ads = [Ad(**item) for item in dummy_data]
            Ad.objects.bulk_create(new_ads)
            print(f"-> Átmásolva {len(new_ads)} autó az Ad táblába.")
            DummyAd.objects.all().delete()
            log.status = "SIKERES (MÁSOLVA)"
            log.actual_scraped = total_saved
            log.save()
            print("MINDEN KÉSZ!")
        except Exception as e:
            print(f"Hiba a másolásnál: {e}")
    else:
        print("❌ HIBA VAGY ÜRES LISTA! Nem nyúlok az éles adatokhoz.")
        DummyAd.objects.all().delete()
        log.save()

if __name__ == "__main__":
    run_scraper()