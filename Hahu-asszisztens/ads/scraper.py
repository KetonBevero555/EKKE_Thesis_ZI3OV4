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
from ads.setup_profile import run_setup

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

# Ár tisztítása (pl. "3 450 000 Ft" -> 3450000)
def clean_price(text: str) -> int | None:
    print(f"Cleaning price from text... {text}")
    if not text: return None
    clean_str = re.sub(r'[^\d]', '', text)
    return int(clean_str) if clean_str else None

# Technikai adatok (évjárat, üzemanyag, stb.) kinyerése
def parse_tech_info(info_elements: list[str]) -> dict:
    print
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

# Egyetlen autó adatainak kinyerése a HTML kártyából
def extract_car_data(card: any) -> dict | None:
    print("Extracting data from a car card...")
    link_el = card.query_selector("h3 a")
    if not link_el: return None
    
    full_url = link_el.get_attribute("href")
    hahu_id = int(full_url.split('-')[-1])

    # Márka & Modell parserek
    parts = full_url.split('/')
    brand = ""; model = ""
    idx = parts.index('szemelyauto')
    if len(parts) > idx + 2:
        brand = parts[idx+1].replace('_', ' ').upper()
        model = parts[idx+2].replace('_', ' ').upper()

    # Árak & Bérlés
    price_primary = card.query_selector(".pricefield-primary")
    price_primary_highlight = card.query_selector(".pricefield-primary-highlighted")
    raw_p = price_primary.inner_text() if price_primary else ""
    raw_ph = price_primary_highlight.inner_text() if price_primary_highlight else ""
    
    is_rentable = "bérelhető" in raw_p.lower()
    no_price = "ár nélkül" in raw_p.lower()
    if is_rentable or no_price:
        return None
        
    final_price = clean_price(raw_p) if raw_p else clean_price(raw_ph)
    if not final_price:
        return None

    # Tech adatok
    info_spans = card.query_selector_all(".talalatisor-info.adatok span.info")
    if not info_spans: info_spans = card.query_selector_all(".talalatisor-info span.info")
    tech = parse_tech_info([span.inner_text() for span in info_spans])

    # Címkék
    tag_spans = card.query_selector_all(".cimke-lista span.label")
    unique_tags = sorted(list(set([t.inner_text() for t in tag_spans if t.inner_text().strip()])))
    tags = "|".join(unique_tags)

    return {
        'hahu_id': hahu_id,
        'brand': brand, 'model': model,
        'price': final_price,
        'fuel': tech['fuel'], 'year': tech['year'],
        'engine_cc': tech['engine_cc'], 'power_le': tech['power_le'], 
        'mileage': tech['mileage'],
        'tags': tags
    }

# Adatbázis művelet
def save_car_to_db(data: dict) -> bool:
    print(f"Saving car to database (hahu_id: {data['hahu_id']})...")
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
    run_setup()

    print("--- STARTING SCRAPER ---")
    
    print("<P> Deleting old dummy data...")
    DummyAd.objects.all().delete()
    
    print("<P> Creating new ScrapeLog entry...")
    log = ScrapeLog.objects.create(status="SCRAPER_STARTED")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "chrome_profile")

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
            time.sleep(5) # Várakozás a teljes betöltődésre
            sb.solve_captcha()

            time.sleep(3) # Várakozás a cookie panel eltűnésére
            print("<P> Clicking the 'Search' button...")
            search_btn = page.wait_for_selector('[data-testid="submit-button"]', state="visible", timeout=45000)
            if search_btn:
                search_btn.click()
                
                if not page.wait_for_selector(".talalati-sor", timeout=30000):
                    raise Exception("Search results failed to load!")
                    
                print("<P> Search results loaded.\nProfile configured! Starting data extraction...")
                log.status = "SCRAPING_IN_PROGRESS"
                log.save()
            else:
                raise Exception("Search button missing!")
            
            page_num = 1
            while True:
                time.sleep(1) # Timeout elleni védelem
                print(f"\n--- PAGE {page_num} ---")

                # Kártyák lekérése
                car_cards = page.query_selector_all(".talalati-sor")
                count_on_page = len(car_cards)
                print(f"[INFO] Ads on page: {count_on_page}")
                
                new_on_page = 0
                updated_on_page = 0
                
                time.sleep(0.5) # Timeout elleni védelem

                # Adatok kinyerése
                for card in car_cards:
                    try:
                        car_data = extract_car_data(card)

                        if car_data is None: continue

                        is_new = save_car_to_db(car_data)

                        if is_new: 
                            new_on_page += 1
                            total_saved += 1
                        else: 
                            updated_on_page += 1
                        
                    except Exception:
                        continue

                # Statisztika
                print(f"[SAVE] Ads saved: {new_on_page}")
                if updated_on_page > 0:
                    print(f"{Colors.YELLOW}[UPDATE] Updated ads: {updated_on_page} {Colors.RESET}")
                print(f"[STATUS] Total saved: {total_saved} cars")

                time.sleep(0.5) # Timeout elleni védelem

                # Lapozás
                next_li = page.query_selector("li.next")
                if (updated_on_page != 0 or new_on_page != 0) or (next_li and "disabled" not in (next_li.get_attribute("class") or "")):
                    next_link = next_li.query_selector("a")
                    if next_link:
                        print(f"Go to page ({page_num + 1})...")
                        next_link.click()
                        page_num += 1
                    else:
                        success = True; break
                else:
                    print("<P> Last useful page reached.")
                    success = True; break
                
                time.sleep(1) # Timeout elleni védelem

                # Várakozás a következő oldal betöltésére
                page.wait_for_selector(".talalati-sor", timeout=60000)
                
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
