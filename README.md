# Hahu-Asszisztens: AI alapú gépjármű-árbecslő alkalmazás

## Jogi és Etikai Nyilatkozat (Disclaimer)

Ez a projekt kizárólag **akadémiai és kutatási célból** készült.  
Kereskedelmi forgalomba nem kerül, és semmilyen formában nem generál bevételt. A dolgozat és a szoftver célja annak vizsgálata, hogy lehetséges-e pontos árbecslő modellt építeni pusztán a nyilvános alapjellemzők (évjárat, teljesítmény, stb.) alapján, a kvalitatív adatok (állapot, szerviztörténet) hiányában.

### A fejlesztés során alkalmazott etikus adatgyűjtési irányelvek:

- **Adatminimalizálás (GDPR):** A rendszer nem gyűjt személyes adatokat (nevek, telefonszámok, pontos címek). Kizárólag a hirdetések nyilvánosan elérhető műszaki paramétereit rögzíti.
- **Terheléskímélő lekérdezés (Rate Limiting):** A scraper modul beépített várakozási időkkel operál, hogy elkerülje a forrásoldal szervereinek túlterhelését.
- **Célhoz kötöttség:** A kinyert adatok kizárólag az AI modellek (**CatBoost** és **Random Forest**) lokális tanítására és tudományos validációjára szolgálnak.

## Fejlesztői megjegyzés a repozitórium tartalmáról

A repozitórium tartalmazza a projekt futtatásához és teszteléséhez szükséges teljes forráskódot (backend, frontend, scraper, AI tanító szkriptek), valamint az előre feltöltött **adatbázist** (`db.sqlite3`), így a historikus hirdetési adatok azonnal rendelkezésre állnak.

**A repozitórium NEM tartalmazza az alábbiakat (ezeket lokálisan kell létrehozni vagy a kód generálja őket):**

- **`.env` fájl**: A rendszer biztonsági beállításai (a mellékelt `.env.example` alapján kell létrehozni).
- **Betanított AI modellek** (`ai/models/`, `ai/backup_models/`): A nagy fájlméret miatt nem kerültek feltöltésre. A modellek (`.pkl` fájlok) az `ai/train.py` futtatásával lokálisan generálódnak le.
- **Scraper munkakönyvtárak** (`chrome_profile/`, `downloaded_files/`): A böngésző munkamenet adatai, melyeket a rendszer az első adatgyűjtéskor automatikusan hoz létre.
- **Futtatási környezet**: A virtuális környezet (`venv/`) és a futtatási gyorsítótárak (`__pycache__/`, `catboost_info/`).

## Technológiai Stack

**Backend:**
- Python 3.13+
- Django
- SQLite (fejlesztési fázisban)

**Adatgyűjtés:**
- Playwright
- SeleniumBase (sb_cdp mód)

**Adattudomány (Machine Learning):**
- CatBoost (Elsődleges gradiens erősítő modell)
- Scikit-learn (Random Forest, TransformedTargetRegressor)
- Pandas & NumPy
- Joblib

**Tesztelés:**
- Django Unit Tests (Backend)
- Cypress (Frontend/E2E)

## Telepítés és Futtatás (Setup)

Az alábbi parancsokat a projekt mappájába belépve kell végrehajtani.

```bash
cd .\Hahu-asszisztens\
```

### 1. Környezet előkészítése

```bash
pip install -r requirements.txt
playwright install chrome
```

### 2. Konfigurációs fájlok beállítása

Készítsen egy másolatot a `.env.example` fájlról `.env` néven, és állítsa be benne a `DJANGO_SECRET_KEY` értékét.

### 3. Adminisztrátor létrehozása

A vezérlőpult elérésére szükség lesz egy fiókra. Ehhez elég csak a felhasználónevet és a jelszót megadni, az e-mail nem fontos hozzá.

```bash
python manage.py createsuperuser  
```

### 4. Modell létrehozása

A betanított AI modell mérete miatt nem része a feltöltött projektnek.

```bash
python .\ai\train.py
```

### 5. Webalkalmazás indítása

```bash
python manage.py runserver  
```

## Tesztelés

Az teszteléshez szükséges parancsokat két mappában lehet használni.

Készítsen egy másolatot a `cypress.env.json.example` fájlról `cypress.env.json` néven, és állítsa be benne a `username` és az `admin_password` értékéit. Ezek az értékek a *superuser* adatai.

**Backend tesztek:**

Alábbi mappában lehet tesztelni a Backend-et.

```bash
cd .\Hahu-asszisztens\
```

Django tesztek futtatása.

```bash
python manage.py test ads  
```

**Frontend (Cypress):**

Alábbi mappában lehet tesztelni a Frontend-et.

```bash
cd .\Cypress-Teszt\
```

Cypress tesztek futtatása.

```bash
npm install  
npx cypress run  
```

## Technikai Korlátok és Rendszerstabilitás

A scraper modul architektúrája kifejezetten a hosszú távú stabilitásra és az adatintegritásra lett optimalizálva:

Historikus adatmegőrzés (Upsert): Az adatbázis-frissítés memóriakímélő `bulk_create` és `bulk_update` logikát használ. A már eladott/levett autók megmaradnak a tanítóhalmazban, a meglévőknél pedig csak a változó adatok (ár, kilométeróra) frissülnek.

Hibatűrés és Watchdog: Hálózati időtúllépések vagy védelmi mechanizmusok (pl. Cloudflare) esetén a rendszer automatikusan újrapróbálkozik. Ha a betöltés végleg elakad, egy "Circuit Breaker" mechanizmus biztonságosan leállítja a folyamatot, megakadályozva a memóriaszivárgást.
