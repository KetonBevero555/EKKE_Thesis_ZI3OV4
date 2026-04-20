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

# Modellek importálása
from ads.models import DummyAd, ScrapeLog, Ad
from ai.train import train_model

# Színek konzol kiíráshoz
class Colors:
    YELLOW = '\033[93m'
    RESET = '\033[0m'

# AdBlock (Kép és Média tiltása) aktiválása az adott oldalon
def activate_adblock(page: any) -> None:
    print("Blocking images and media...")
    def route_intercept(route: any) -> None:
        if route.request.resource_type in ["image", "media"]:
            route.abort()
        else:
            route.continue_()
    page.route("**/*", route_intercept)

# Ár tisztítása
def clean_price(text: str) -> int | None:
    if not text: return None
    clean_str = re.sub(r'[^\d]', '', text)
    return int(clean_str) if clean_str else None

# Technikai adatok (évjárat, üzemanyag, stb.) kinyerése
def parse_tech_info(info_elements: list[str]) -> dict:
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
        elif 'benzin' in text_lower and 'lpg' not in text_lower:
            data['fuel'] = 'Benzin'
        elif 'dízel' in text_lower or 'diesel' in text_lower:
            data['fuel'] = 'Dízel'
        elif 'elektromos' in text_lower:
            data['fuel'] = 'Elektromos'
        elif 'hibrid' in text_lower:
            data['fuel'] = 'Hibrid'
        elif 'lpg' in text_lower:
            data['fuel'] = 'LPG'
        elif 'cng' in text_lower:
            data['fuel'] = 'CNG'
        elif 'cm³' in raw_text:
            data['engine_cc'] = int(re.sub(r'[^\d]', '', raw_text))
        elif 'kW' in raw_text:
            data['power_kw'] = int(re.sub(r'[^\d]', '', raw_text.split('kW')[0]))
        elif 'LE' in raw_text:
            data['power_le'] = int(re.sub(r'[^\d]', '', raw_text.split('LE')[0]))
        elif 'km' in raw_text and 'km-re' not in text_lower:
            data['mileage'] = int(re.sub(r'[^\d]', '', raw_text))
            
    return data

# Tartalom betöltése Retry (Újrapróbálkozás) logikával
# Visszatér True-val ha sikerült, False-al ha végleges timeout
def wait_for_content(page: any, selector=".talalati-sor", attempts=3, timeout=45000) -> bool:
    for attempt in range(1, attempts + 1):
        try:
            page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"[!] TIMEOUT! Reloading the page... Attempt ({attempt}/{attempts})")
            page.reload()
            time.sleep(5)
    return False

# Egyetlen autó adatainak kinyerése a HTML kártyából
def extract_car_data(card: any) -> dict | None:
    link_el = card.query_selector("h3 a")
    if not link_el: return None
    
    full_url = link_el.get_attribute("href")
    title = link_el.inner_text()
    hahu_id = int(full_url.split('-')[-1])

    # Márka & Modell parserek
    parts = full_url.split('/')
    brand = ""; model = ""
    idx = parts.index('szemelyauto')
    if len(parts) > idx + 2:
        brand = parts[idx+1].replace('_', ' ').title()
        model = parts[idx+2].replace('_', ' ').title()

    # Árak & Bérlés
    price_primary = card.query_selector(".pricefield-primary")
    price_secondary = card.query_selector(".pricefield-secondary-basic")
    raw_p1 = price_primary.inner_text() if price_primary else ""
    raw_p2 = price_secondary.inner_text() if price_secondary else ""
    
    is_rentable = "bérelhető" in raw_p1.lower() or "bérelhető" in raw_p2.lower()
    p1 = clean_price(raw_p1); p2 = clean_price(raw_p2)
    final_price = p1
    sale_price = p2 if p2 else None

    # Tech adatok
    info_spans = card.query_selector_all(".talalatisor-info.adatok span.info")
    if not info_spans: info_spans = card.query_selector_all(".talalatisor-info span.info")
    tech = parse_tech_info([span.inner_text() for span in info_spans])

    # Címkék
    tag_spans = card.query_selector_all(".cimke-lista span.label")
    unique_tags = sorted(list(set([t.inner_text() for t in tag_spans if t.inner_text().strip()])))
    tags = "|".join(unique_tags)

    # Leírás & Eladó
    desc_el = card.query_selector(".talalati-sor__leiras")
    description = desc_el.inner_text() if desc_el else ""
    seller_el = card.query_selector(".trader-name")
    seller = seller_el.inner_text().replace("Kereskedés: ", "") if seller_el else "Magánszemély"

    return {
        'hahu_id': hahu_id, 'url': full_url, 'title': title, 
        'brand': brand, 'model': model,
        'price': final_price, 'sale_price': sale_price, 'is_rentable': is_rentable,
        'fuel': tech['fuel'], 'year': tech['year'], 'month': tech['month'],
        'engine_cc': tech['engine_cc'], 'power_le': tech['power_le'], 
        'power_kw': tech['power_kw'], 'mileage': tech['mileage'],
        'tags': tags, 'description_snippet': description, 'seller': seller,
        'no_price': True if not final_price else False
    }

# Adatbázis művelet
def save_car_to_db(data: dict) -> bool:
    obj, created = DummyAd.objects.update_or_create(
        hahu_id=data['hahu_id'],
        defaults=data
    )
    return created

# Adatok átmásolása az Ad táblába
def finalize_migration(log: ScrapeLog) -> None:
    print("\n================================================")
    dummy_count = DummyAd.objects.count()
    if dummy_count > 0:
        print(f"SCRAPER FINISHED! Found {dummy_count} cars. Starting migration...")
        try:
            Ad.objects.all().delete()
            dummy_data = DummyAd.objects.values().exclude(id__isnull=True)
            new_ads = [Ad(**item) for item in dummy_data]
            Ad.objects.bulk_create(new_ads)
            final_ad_count = Ad.objects.count()
            print(f"<P> -> Copied {final_ad_count} cars to the Ad table.")

            DummyAd.objects.all().delete()
            log.status = "SUCCESS"
            log.actual_scraped = final_ad_count
            log.end_time = timezone.now()
            log.save()
            print("<P> Log saved with SUCCESS status.")
            
        except Exception as e:
            print(f"<!> Error occurred while saving log: {e}")
            log.status = f"MIGRATION_ERROR: {str(e)}"
            log.end_time = timezone.now()
            log.save()
    else:
        print("<!> Error occurred, no data in Dummy table to save.")
        log.status = "NO_DATA_SCRAPED"
        log.actual_scraped = 0
        log.end_time = timezone.now()
        log.save()

# Fő futtató metódus
def run_scraper():
    print("--- STARTING SCRAPER ---")
    
    print("<P> Deleting old dummy data...")
    DummyAd.objects.all().delete()
    
    print("<P> Creating new ScrapeLog entry...")
    log = ScrapeLog.objects.create(expected_cars=0, status="SCRAPER_STARTED")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "chrome_profile")
    
    if os.path.exists(profile_dir):
        print(f"[*] Deleting old profile: {profile_dir}...")
        try:
            shutil.rmtree(profile_dir)
            print("[*] Old profile deleted successfully!")
        except Exception as e:
            print(f"[!] Error occurred while deleting the profile: {e}")
            log.status = f"CRITICAL_ERROR: Profile deletion failed: {e}"
            log.save()
            return
    
    print(f"[*] Creating new profile folder here: {profile_dir}")

    try:
        sb = sb_cdp.Chrome(user_data_dir=profile_dir, incognito=False, headless=False)
        endpoint = sb.get_endpoint_url()
        print(f"<P> Browser is running. Endpoint: {endpoint}")
    except Exception as e:
        print(f"[!] Error starting browser: {e}")
        log.status = f"CRITICAL_ERROR: Browser start failed: {e}"
        log.save()
        return

    success = False
    total_saved = 0

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(endpoint)
            context = browser.contexts[0]
            page = context.pages[0]

            print("<P> Starting the homepage...")
            page.goto("https://www.hasznaltauto.hu/")
            
            print("<P> Waiting/Captcha verification...")
            sb.solve_captcha()

            print("<P> Searching for cookie panel...")
            cookie_accepted = False
            for _ in range(10):
                try:
                    agree_btn = page.query_selector("#didomi-notice-agree-button")
                    if agree_btn and agree_btn.is_visible():
                        agree_btn.click(force=True)
                        print("<P> Cookies accepted successfully!")
                        cookie_accepted = True
                        break
                except:
                    pass
                time.sleep(2)
            
            if not cookie_accepted:
                print("<P> Cookie panel not found!")

            time.sleep(3) # Várakozás a cookie panel eltűnésére
            print("<P> Clicking the 'Search' button...")
            search_btn = page.query_selector('[data-testid="submit-button"]')
            if search_btn:
                search_btn.click()
                
                if not wait_for_content(page):
                    raise Exception("Search results failed to load!")
                    
                print("<P> Search results loaded.\nProfile configured! Starting data extraction...")
                log.status = "SCRAPING_IN_PROGRESS"
                log.save()
            else:
                raise Exception("Search button missing!")
            
            page_num = 1
            while True:
                time.sleep(1) # Tiltás elleni védelem
                print(f"\n--- PAGE {page_num} ---")

                # Kártyák lekérése
                car_cards = page.query_selector_all(".talalati-sor")
                count_on_page = len(car_cards)
                print(f"[INFO] Ads on page: {count_on_page}")
                
                new_on_page = 0
                updated_on_page = 0
                
                time.sleep(0.5) # Tiltás elleni védelem

                # Adatok kinyerése
                for card in car_cards:
                    try:
                        car_data = extract_car_data(card)
                        if not car_data: continue

                        is_new = save_car_to_db(car_data)
                        if is_new: new_on_page += 1
                        else: updated_on_page += 1
                        total_saved += 1
                    except Exception:
                        continue
                
                time.sleep(0.5) # Tiltás elleni védelem

                # Statisztika
                print(f"[SAVE] Ads saved: {new_on_page}")
                if updated_on_page > 0:
                    print(f"{Colors.YELLOW}[UPDATE] Updated ads: {updated_on_page} {Colors.RESET}")
                print(f"[STATUS] Total saved: {total_saved} cars")

                time.sleep(0.5) # Tiltás elleni védelem
                
                # Lapozás
                next_li = page.query_selector("li.next")
                if next_li and "disabled" not in (next_li.get_attribute("class") or ""):
                    next_link = next_li.query_selector("a")
                    if next_link:
                        print(f"Go to page ({page_num + 1})...")
                        next_link.click()
                        page_num += 1
                    else:
                        success = True; break
                else:
                    print("<P> Last page reached.")
                    success = True; break
                
                time.sleep(1) # Tiltás elleni védelem

                # Várakozás a következő oldal betöltésére
                page.wait_for_selector(".talalati-sor", timeout=30000)
                
            
        except Exception as e:
            print(f"<P> Critical error occurred: {e}")
            log.status = f"CRITICAL_ERROR: {str(e)}"
            log.save()
        finally:
            print("<P> Closing the browser...")
            try:
                browser.close() # Playwright böngésző bezárása
                sb.driver.quit() # SeleniumBase driver bezárása (Ha a Playwright nem zárta volna be az oldalt)
            except:
                pass

    if success:
        finalize_migration(log)
        try:
            train_model()
        except Exception as e:
            print(f"<!> Error starting AI training: {e}")
    else:
        print("<!> Error or interrupted execution! Check logs.")
        log.actual_scraped = DummyAd.objects.count()
        log.end_time = timezone.now()
        log.save()

if __name__ == "__main__":
    run_scraper()
