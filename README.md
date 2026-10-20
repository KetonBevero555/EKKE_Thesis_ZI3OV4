# Hahu-Asszisztens: AI alapú gépjármű-árbecslő alkalmazás

## Jogi és Etikai Nyilatkozat (Disclaimer)

Ez a projekt kizárólag **akadémiai és kutatási célból** készült.  
Kereskedelmi forgalomba nem kerül, és semmilyen formában nem generál bevételt.

### A fejlesztés során alkalmazott etikus adatgyűjtési irányelvek:

- **Adatminimalizálás (GDPR):**
  A rendszer nem gyűjt személyes adatokat (nevek, telefonszámok, pontos címek).  
  Kizárólag a hirdetések nyilvánosan elérhető műszaki paramétereit rögzíti.

- **Terheléskímélő lekérdezés (Rate Limiting):** 
  A scraper modul beépített várakozási időkkel operál, hogy elkerülje a forrásoldal szervereinek túlterhelését.

- **Célhoz kötöttség:**  
  A kinyert adatok kizárólag a **Random Forest Regressor** modell lokális tanítására és tudományos validációjára szolgálnak.

## Fejlesztői megjegyzés a repozitórium tartalmáról

A biztonsági és tárhelykezelési irányelvek miatt az alábbi fájlok **nem részei a tárolónak**, ezeket lokálisan kell létrehozni a futtatáshoz:

- `.env` → Django biztonsági beállítások (sablon: `.env.example`)

- `cypress.env.json` → Frontend teszt jelszó (sablon: `cypress.env.json.example`)

- `db.sqlite3` → Adatbázis fájl (automatikusan létrejön migráció során)

- `node_modules/` → A Cypress futtatásához szükséges könyvtárak (telepítés: `npm install`)

## Technológiai Stack

**Backend:**
- Python 3.13+
- Django
- SQLite (fejlesztési fázisban)

**Adatgyűjtés:**
- Playwright
- SeleniumBase (sb_cdp mód)

**Adattudomány:**
- Scikit-learn (Random Forest)
- Pandas
- Joblib

**Tesztelés:**
- Django Unit Tests (Backend)
- Cypress (Frontend/E2E)

## Telepítés és Futtatás (Setup)

### 1. Környezet előkészítése

A `requirements.txt`-vel egy mappában kell lenni, hogy feltelepüljenek a python könyvtárak

```bash

pip install -r requirements.txt  
playwright install chrome  
```

### 2. Konfigurációs fájlok beállítása

Másolja le a `.env.example` fájlt `.env` néven, és állítsa be a `DJANGO_SECRET_KEY` értékét.

Lépjen a Cypress-Teszt mappába, és másolja le a `cypress.env.json.example` fájlt `cypress.env.json` néven, kitöltve a teszt jelszóval.

### 3. Adatbázis és Adminisztráció

```bash
python manage.py makemigrations  
python manage.py migrate  
python manage.py createsuperuser  
```

### 4. Adatgyűjtés és Modellfrissítés

Az adatgyűjtő folyamat elindítása a projekt gyökeréből:

```bash
python ads/scraper.py  
```

**Megjegyzés:**  
A folyamat végén a rendszer automatikusan lefuttatja az MI modell újratanítását (`train.py`), mely során:

- numerikus skálázást alkalmaz (**StandardScaler**)  
- outlier-szűrést végez (**200 000 Ft – 100 000 000 Ft** tartományban)

### 5. Webalkalmazás indítása

```bash
python manage.py runserver  
```

## Tesztelés

**Backend tesztek:**  

```bash
python manage.py test ads  
```

**Frontend (Cypress):**

```bash
cd Cypress-Teszt  
npm install  
npx cypress run  
```

## Technikai Korlátok és Stabilitás

Az adatgyűjtési sebesség az optimalizálások után elérte a ~7 s/oldal értéket.

Fontos kiemelni, hogy a hálózati architektúra és a forrásoldali védelmi mechanizmusok miatt a folyamat során felléphetnek időtúllépések (Timeout).

A rendszer **hibatűrő**:
- érvénytelen rekord → kihagyás  
- nem várt HTML-struktúra → továbblépés
