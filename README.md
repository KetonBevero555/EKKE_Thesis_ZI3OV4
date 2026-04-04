# Szakdolgozat

## Jogi és Etikai Nyilatkozat (Disclaimer)

Ez a projekt kizárólag **akadémiai, oktatási és kutatási célból** (egyetemi szakdolgozat) készült. Kereskedelmi forgalomba nem kerül, és semmilyen formában nem generál bevételt.

A projekt fejlesztése és működése során kiemelt figyelmet kapott az etikus adatkezelés:
* **Személyes adatok védelme (GDPR):** A web-scraper algoritmus **egyetlen személyes adatot sem gyűjt**. Nevek, telefonszámok, pontos címek vagy egyéb azonosításra alkalmas adatok nem kerülnek letöltésre. A rendszer kizárólag a járművek nyilvánosan elérhető technikai paramétereit (márka, modell, évjárat, ár, stb.) rögzíti a listázó oldalakról.
* **Publikus adatok:** A feldolgozott adatok bárki számára, bejelentkezés nélkül hozzáférhető, publikus adatok.
* **Szerzői jogok tiszteletben tartása:** Etikai és jogi megfontolásokból ez a GitHub tároló **nem tartalmazza** a kinyert adatbázist, a betanított Mesterséges Intelligencia modellt, valamint a működéshez szükséges böngészőprofilokat. A repóban kizárólag a kutatáshoz írt forráskód található meg.

---

## Készítő
- **Készítő:** Takács Márk
- **Neptun kód:** ZI3OV4
- **Szak:** Programtervező informatikus BSc

## Szakdolgozati téma
AI alapú modern webalkalmazás fejlesztése

## Szakdolgozat célja
Autó árbecslő, a Használtautó.hu adatai alapján betanított Mesterséges Intelligencia (MI) segítségével.

---

## Használt technológiák

**Frontend (Kliens oldal):**
* HTML5, CSS3, JavaScript (AJAX a dinamikus űrlapokhoz)
* Bootstrap 5 (Reszponzív dizájn, kártyák, UI elemek)
* Bootstrap Icons (Letisztult, modern ikonográfia)

**Backend (Szerver oldal):**
* Python 3.13.3
* Django (Webes keretrendszer, ORM, Adminisztrációs felület és Hitelesítés)
* SQLite (Könnyűsúlyú, lokális relációs adatbázis)

**Adatgyűjtés és Automatizáció (Web Scraping):**
* Playwright (Aszinkron, nagy sebességű webkaparás és tartalomkinyerés)
* SeleniumBase (`sb_cdp` modul - Cloudflare és Captcha botvédelmek automatikus megkerülése)

**Mesterséges Intelligencia (Machine Learning & Data Science):**
* Pandas (Adattisztítás, adatelőkészítés és kiugró értékek kezelése)
* Scikit-Learn (Random Forest Regressor algoritmus, Pipeline, One-Hot Encoding)
* Joblib (A betanított ML modell sorosítása és visszatöltése a webes kérésekhez)

---

## Adatgyűjtés és MI Tanítás

Fontos technikai tudnivalók a futtatásról:

Folyamat hossza: Az adatgyűjtés átlagosan 10-11 órát vesz igénybe, mert a használtautók.hu-t a CloudFlare védi és minden egyes oldalon egyesével kell végigmennie.

Hálózati stabilitás: Kifejezetten ajánlott a stabil, vezetékes internetkapcsolat használata! A tesztelési fázisban bebizonyosodott, hogy a WiFi hálózatok apró, tizedmásodperces mikro-szakadásaiból adódóan a scraper több száz oldalnyi adatgyűjtés után időtúllépés (Timeout) miatt megállhat.

Teljes automatizáció: A folyamat emberi beavatkozást nem igényel. A szkript felépíti a tiszta böngészőprofilt, letölti a friss hirdetéseket, áttölti őket az éles adatbázisba, majd a legvégén automatikusan elindítja az MI modell újra-tanítását a legújabb árakkal.

## Weboldalcímek

http://127.0.0.1:8000/
http://127.0.0.1:8000/dashboard/
(Megjegyzés: /dashboard/ oldalra belépés szükséges a 6. pontban létrehozott admin profil segítségével.)

---

## Projekt előkészítése a működéshez (Setup)

Az alábbi lépésekkel a projekt a nulláról felállítható és futtatható bármilyen lokális (helyi) fejlesztői környezetben.

### 1. A tároló (Repository) klónozása

Nyisd meg a parancssort (Terminal / Git Bash / PowerShell) és klónozd vagy töltsd le a projektet a gépedre

### 2. **(Nem kötelező)** Virtuális környezet (venv) létrehozása és aktiválása

A virtuális környezet biztosítja, hogy a projekt csomagjai elszeparálva működjenek a géped többi Python csomagjától. Nyiss egy parancssort a projekt mappájában, és futtasd az alábbiakat:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Függőségek (Python csomagok) telepítése

Telepítsd a fejlesztéshez használt könyvtárakat a virtuális környezetbe az alábbi paranccsal:

```bash
pip install django pandas scikit-learn playwright seleniumbase joblib
```
### 4. Böngésző követelmény

Mivel az adatgyűjtő automatika (SeleniumBase) a rendszer natív böngészőjét használja, győződj meg róla, hogy a **Google Chrome** fel van telepítve a gépedre.

### 5. Adatbázis felépítése (Migrációk)

A Django tábláinak (DummyAd, Ad, ScrapeLog, AILog) létrehozása az SQLite adatbázisban:

```bash
python manage.py makemigrations ads
python manage.py migrate
```

### 6. Admin felhasználó létrehozása (Vezérlőpult eléréséhez)

A statisztikai felület és a privát Dashboard megtekintéséhez készíteni kell egy adminisztrátor fiókot:

```bash
python manage.py createsuperuser
```

### 7. A webes szerver elindítása

```bash
python manage.py runserver
```
(Megjegyzés: Mivel az adatbázis üres, így nem tud becslést adni és a /dashboard/ oldalon sem fognak megjelenni adatok.)

### +1. Adatgyűjtés indítása és MI modell tanítása

```bash
python ./Hahu-asszisztens/ads/scraper.py
```
