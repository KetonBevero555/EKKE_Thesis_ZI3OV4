import os
import django
import re
import time
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

# 1. Django környezet betöltése
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hahu_backend.settings')
django.setup()

from ads.models import DummyAd, ScrapeLog

# --- SEGÉDFÜGGVÉNYEK ADATTISZTÍTÁSHOZ ---

def clean_price(text):
    """Szöveges ár (14 300 000 Ft) átalakítása számmá (14300000)"""
    if not text:
        return None
    # Kitöröljük a nem számjegyeket (szóköz, Ft, stb.)
    clean_str = re.sub(r'[^\d]', '', text)
    return int(clean_str) if clean_str else None

def parse_tech_info(info_elements):
    """
    A 'Benzin, 2025/1, 1 199 cm³, 136 LE' listából kinyeri az adatokat.
    Bemenet: lista a span.info elemek szövegeivel.
    """
    data = {
        'fuel': None, 'year': None, 'month': None, 
        'engine_cc': None, 'power_le': None, 'power_kw': None, 'mileage': None
    }
    
    # Mivel a sorrend nem mindig fix, mintákra (regex) keresünk minden elemnél
    for item in info_elements:
        text = item.strip().replace('\xa0', ' ') # Nem törő szóközök cseréje
        
        # 1. Évjárat (pl. 2025/1 vagy simán 2024)
        if '/' in text and re.search(r'\d{4}/\d{1,2}', text):
            parts = text.split('/')
            data['year'] = int(re.sub(r'[^\d]', '', parts[0]))
            data['month'] = int(re.sub(r'[^\d]', '', parts[1]))
        elif re.match(r'^\d{4}$', text): # Csak évszám
            data['year'] = int(text)

        # 2. Köbcenti (cm³)
        elif 'cm³' in text:
            data['engine_cc'] = int(re.sub(r'[^\d]', '', text))

        # 3. Teljesítmény (kW és LE - néha egyben van, néha külön)
        elif 'kW' in text:
            val = int(re.sub(r'[^\d]', '', text.split('kW')[0]))
            data['power_kw'] = val
        elif 'LE' in text:
            val = int(re.sub(r'[^\d]', '', text.split('LE')[0]))
            data['power_le'] = val
            
        # 4. Kilométeróra (km)
        elif 'km' in text and not 'km-re' in text: # A "km-re" a távolság, nem a futás!
            data['mileage'] = int(re.sub(r'[^\d]', '', text))
            
        # 5. Üzemanyag (Ha nem szám, és benne van a listában)
        elif text in ['Benzin', 'Dízel', 'Benzin/LPG', 'Hibrid', 'Hibrid (Benzin)', 'Elektromos', 'LPG']:
            data['fuel'] = text

    return data

# --- FŐ SCRAPER LOGIKA ---

def run_scraper():
    print("Scraper indítása...")
    # Log bejegyzés
    log = ScrapeLog.objects.create(expected_cars=0, status="INDULAS")
    
    sb = sb_cdp.Chrome()
    endpoint_url = sb.get_endpoint_url()
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint_url)
        context = browser.contexts[0]
        page = context.pages[0]

        try:
            # 1. Oldalnyitás és Captcha
            print("Főoldal betöltése...")
            page.goto("https://www.hasznaltauto.hu/")
            sb.sleep(3)
            sb.solve_captcha() # Cloudflare kezelés
            
            # 2. Keresés gomb megnyomása
            print("Keresés indítása...")
            page.click("button.btn-search")
            sb.sleep(4) # Várunk, hogy betöltsön a lista
            sb.solve_captcha() # Biztonsági ellenőrzés

            # 3. Adatgyűjtés az ELSŐ oldalról
            print("Elemzés kezdése...")
            
            # Az összes autókártya begyűjtése
            car_cards = page.query_selector_all(".talalati-sor")
            print(f"Talált autók száma az oldalon: {len(car_cards)}")
            
            saved_count = 0
            
            for card in car_cards:
                try:
                    # --- URL és ID ---
                    link_el = card.query_selector("h3 a")
                    if not link_el: continue # Ha reklám vagy egyéb, átugorjuk
                    
                    full_url = link_el.get_attribute("href")
                    title = link_el.inner_text()
                    
                    # ID kinyerése a végéről (pl. ...-21647701)
                    hahu_id = int(full_url.split('-')[-1])
                    
                    # Brand/Model az URL-ből (opcionális, de jó ha van)
                    url_parts = full_url.split('/')
                    # Általában: .../szemelyauto/marka/modell/...
                    brand = url_parts[4].capitalize() if len(url_parts) > 4 else "Egyéb"
                    model = url_parts[5].capitalize() if len(url_parts) > 5 else "Egyéb"

                    # --- ÁRAK ---
                    price_el = card.query_selector(".pricefield-primary")
                    sale_price_el = card.query_selector(".pricefield-secondary-basic")
                    
                    raw_price = price_el.inner_text() if price_el else None
                    raw_sale = sale_price_el.inner_text() if sale_price_el else None
                    
                    price = clean_price(raw_price)
                    sale_price = clean_price(raw_sale) # Ha van akciós ár, azt ide tesszük
                    
                    # Ha van akciós ár, a sima ár mezőbe az eredeti kerüljön? 
                    # A te logikád szerint: price = eredeti, sale_price = akciós
                    
                    # --- TECHNIKAI ADATOK ---
                    # Kigyűjtjük az összes span.info szövegét egy listába
                    info_spans = card.query_selector_all(".talalatisor-info.adatok span.info")
                    info_texts = [span.inner_text() for span in info_spans]
                    tech_data = parse_tech_info(info_texts)
                    
                    # --- CÍMKÉK (TAGS) ---
                    # | jellel elválasztva gyűjtjük őket
                    tag_spans = card.query_selector_all(".cimke-lista span.label")
                    tags_list = [t.inner_text() for t in tag_spans]
                    tags_string = "|".join(tags_list)

                    # --- MENTÉS ADATBÁZISBA ---
                    DummyAd.objects.update_or_create(
                        hahu_id=hahu_id,
                        defaults={
                            'url': full_url,
                            'brand': brand,
                            'model': model,
                            'title': title,
                            'price': price,
                            'sale_price': sale_price,
                            'fuel': tech_data['fuel'],
                            'year': tech_data['year'],
                            'month': tech_data['month'],
                            'engine_cc': tech_data['engine_cc'],
                            'power_le': tech_data['power_le'],
                            'power_kw': tech_data['power_kw'],
                            'mileage': tech_data['mileage'],
                            'tags': tags_string,
                            'no_price': False if price else True
                        }
                    )
                    saved_count += 1
                    print(f"[OK] Mentve: {title} ({price} Ft)")

                except Exception as e:
                    print(f"[HIBA] Egy autót nem sikerült feldolgozni: {e}")
                    continue

            # Log frissítése
            log.status = "SIKERES (1. oldal)"
            log.actual_scraped = saved_count
            log.save()
            print("Kész! Ellenőrizd az adatbázist.")

        except Exception as e:
            print(f"Kritikus hiba: {e}")
            log.status = f"CRITICAL: {str(e)}"
            log.save()
        finally:
            sb.quit()

if __name__ == "__main__":
    run_scraper()
