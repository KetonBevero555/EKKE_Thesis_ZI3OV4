# Részletes Fejlesztési Napló (Hahu-asszisztens)

## Scraper alapok és védelem megkerülése

Mit fejlesztettem: Az alap robotot, ami letölti a weboldalakat. Kezdetben egy egyszerű requests könyvtárral próbálkoztam, hogy elérjem a Hahu-t.

Ha működött és van eredménye milyen lett: Végül sikerült elérni, hogy a rendszer egy valós felhasználónak higgye a programot, így zavartalanul tud futni.

Ha hiba volt vele milyen hibák voltak vele: Az alap módszerrel a Cloudflare és a Captcha védelem azonnal blokkolta a robotot. A GDPR és Cookie elfogadó ablakok is folyton felugrottak, ami megakasztotta a folyamatot. Ráadásul a projekt mappa tele lett szemetelve letöltött és ideiglenes fájlokkal.

Mivel javítottam ki a hibákat: Bevezettem a seleniumbase CDP módját, ami egy valós böngészőt szimulál. Beállítottam egy állandó (perzisztens) Chrome profilt (user_data_dir), így a gép megjegyezte a süti beállításokat, és többet nem dobált ki. A szemetelést úgy oldottam meg, hogy a felesleges mappákat (pl. downloaded_files és az AI modellek helyét) beletettem a .gitignore fájlba.

## Adatok kinyerése és formázása (Parsing)

Mit fejlesztettem: A letöltött weboldalak HTML kódjából kinyertem a konkrét autóadatokat (márka, modell, ár, évjárat, köbcenti, stb.).

Ha működött és van eredménye milyen lett: A végére teljesen tiszta, adatbázisba menthető, szétválasztott adatokat (pl. 2000 cm³, Dízel, 2018) és matematikailag kezelhető árakat kaptam, 100%-os márka- és modellfelismeréssel.

Ha hiba volt vele milyen hibák voltak vele: A weboldal HTML szerkezete eléggé kaotikus volt, így a márka és a modell sokszor "Unknown" lett. A technikai adatok egybe voltak ömlesztve egy szövegbe, a felszereltség címkéknél pedig duplikációk lettek. Az áraknál a szóközök és a "Ft" miatt a gép szövegként kezelte a számokat, a bérautókat pedig "Ár nélkülinek" érzékelte.

Mivel javítottam ki a hibákat: A márkát és modellt inkább egyből az URL linkből vágtam ki, mert az sokkal megbízhatóbb. A technikai adatokhoz írtam külön Regex (reguláris kifejezés) szabályokat, a címkéknél pedig set() használatával szűrtem ki a duplikációkat. Írtam egy clean_price függvényt, ami kipucolja a betűket az árakból, és létrehoztam egy is_rentable logikai mezőt a bérlős autók megkülönböztetésére.

## Sebesség optimalizálás és hálózati stabilitás

Mit fejlesztettem: A scraper gyorsítását, mivel alapból 4-5 másodperc volt egy oldal letöltése a reklámok és képek miatt, ami 90 ezer autónál napokig tartott volna.

Ha működött és van eredménye milyen lett: Sikerült a betöltési időt 2 másodperc alá csökkenteni, ráadásul a robot sokkal stabilabb lett hosszú távon is.

Ha hiba volt vele milyen hibák voltak vele: Először megpróbáltam mindent letiltani a betöltésnél (scriptek, betűtípusok, képek), de emiatt az oldal teljesen lefagyott ("homokórázott") és nem ment a keresés. Később, amikor már gyors volt a kód, 200 oldal után véletlenszerűen Timeout (időtúllépés) hibákkal leállt az egész.

Mivel javítottam ki a hibákat: Bevezettem a "Safe Turbo Mode"-ot: a kód működéséhez kellő scripteket engedélyeztem, csak a nagy méretű képeket és videókat tiltottam le. A Timeout hibánál rájöttem, hogy a WiFi okoz apró, tizedmásodperces csomagvesztéseket (mikro-szakadások), amit a robot nem bírt el. Átdugtam a gépet kábeles (Ethernet) netre, és a Timeout hiba azonnal megszűnt.

## Verziókövetés és kód visszaállítás (Git / GitHub használat)

Mit fejlesztettem: Amikor a scraper sebességét próbáltam a végletekig felgyorsítani, letiltottam egy csomó mindent (scripteket, fontokat), ezt a módosítást pedig elmentettem, és fel is küldtem (git push) a GitHub tárolómba, azt gondolva, hogy kész vagyok.

Ha működött és van eredménye milyen lett: A kód visszaállítása után azonnal újra volt egy stabil, működő alapom. Pillanatok alatt folytatni tudtam a munkát anélkül, hogy a teljes projekt tönkrement volna. Ez a gyakorlatban bebizonyította, hogy a Git verziókövetés életmentő, ha az ember elront valamit.

Ha hiba volt vele milyen hibák voltak vele: A túlzott tiltás miatt a weboldal egyáltalán nem töltött be, "deadlock" (teljes lefagyás) állapotba került. Mivel a módosítást már felküldtem (pusholtam), a hivatalos kódom teljesen használhatatlanná vált, a robot pedig megállt.

Mivel javítottam ki a hibákat: Ahelyett, hogy elkezdtem volna kézzel visszatörölgetni a kódsorokat vagy emlékezetből javítgatni, a Git verziókövetőt használtam. Csináltam egy Git állapot visszatöltést, amivel visszaugrottam a legutolsó, még tökéletesen működő commitra (verzióra). Így egyetlen paranccsal visszakaptam a működő scraperemet.

## Hálózati stabilitás és a "Timeout" rejtély (Kábeles net)

Mit fejlesztettem: A scraper folyamatos, megszakítás nélküli futását nagy mennyiségű (pl. több ezer autó) adat kinyerésekor.

Ha működött és van eredménye milyen lett: A rendszer most már stabilan, órákig képes futni fagyás vagy leállás nélkül, a timeout hibák teljesen megszűntek.

Ha hiba volt vele milyen hibák voltak vele: Hiába optimalizáltam a kódot és írtam bele újrapróbálkozós (Retry) logikát, a 200. oldal környékén a robot sokszor véletlenszerűen "Timeout" (időtúllépés) hibával leállt, és nem tudta folytatni a munkát.

Mivel javítottam ki a hibákat: Rájöttem, hogy nem a kód a rossz, hanem a WiFi kapcsolat okoz apró csomagvesztéseket (mikro-szakadások). Mivel a robot ezredmásodperces pontossággal várja a weboldal elemeinek betöltését, egy pici net-kihagyás is végzetes volt neki. Amint átdugtam a laptopot kábeles (Ethernet) netre, az adatfolyam stabil lett, és a hiba azonnal megszűnt.

## Adatbázis mentés és hibatűrés

Mit fejlesztettem: Az adatok adatbázisba írását és a scraper önálló, hiba esetén is továbbműködő (Retry) logikáját.

Ha működött és van eredménye milyen lett: A program bármikor újraindítható, az adatbázis mindig a valós, aktuális piaci állapotot tükrözi. A konzol kimenete pedig szép, átlátható és színezett lett.

Ha hiba volt vele milyen hibák voltak vele: Lapozás közben, ahogy új autók kerültek fel, elcsúszott a lista, és a program elszállt, ha már létező autót akart újra elmenteni. A szerver lassulásakor a gép feladta a várakozást. A legnagyobb baj pedig az volt, hogy ha frissítettem is az adatokat, a már eladott (törölt) autók örökre bennragadtak az adatbázisomban.

Mivel javítottam ki a hibákat: Sima létrehozás helyett update_or_create funkciót használtam, így az ismétlődéseket csak frissíti. A szerver lassulások ellen beállítottam 45 másodperc várakozási időt, és egy 3x-os újrapróbálkozást. Az eladott autók problémáját a "Clean Slate" (tiszta lap) módszerrel oldottam meg: a robot először egy ideiglenes Dummy táblába gyűjt, és csak ha végzett, akkor üríti ki az éles táblát és másolja át a friss adatokat.

## Mesterséges Intelligencia és Weboldal

Mit fejlesztettem: Eredetileg nagy nyelvi modellt (LLM) és komplex felhasználókezelést terveztem, de a konzulenssel egyeztetve a fókuszt egy okos, saját adaton tanított Árbecslő modellre (Random Forest algoritmus) és a hozzá tartozó weboldalra váltottam.

Ha működött és van eredménye milyen lett: Készítettem egy működőképes, egyszerű, de jól használható weboldalt. A modell az első teszteken, valid adatokkal meglepően jól, 0.93-as R2 Score pontossággal és ~1.100.000 Ft-os átlagos tévedéssel árazta be az autókat.

Ha hiba volt vele milyen hibák voltak vele: Amikor a kódot szerveztem, a fájlok és a kimentett AI modellek (.pkl fájlok) elérési útvonalaival voltak relatív útvonal hivatkozási hibák, a kód nem találta a Django projektet.

Mivel javítottam ki a hibákat: Létrehoztam egy teljesen külön ai mappát a tanító scriptnek és a kimentett modelleknek, és Python kód szintjén (sys.path.append) kötöttem össze a háttérrendszerrel a fájlokat. Ezzel a projekt szerkezete is sokkal letisztultabb lett.

## A Mesterséges Intelligencia (AI) okosítása és finomhangolása

Mit fejlesztettem: Továbbfejlesztettem az árbecslő AI-t, hogy ne csak az autók márkáját, hanem a pontos típusát (modelljét) is ismerje, és mindezt egy új, adatbázisban tárolt napló (AILog) rögzítse. Ezt összekötöttem a weboldallal is egy dinamikus legördülő menüvel.

Ha működött és van eredménye milyen lett: Az AI pontossága (R2 Score) felment közel 0.94-re, az átlagos tévedése pedig lecsökkent 1,1 millióról 924 000 Forintra. A weboldal is profibb lett: ha kiválasztok egy márkát, csak a hozzá tartozó modellek jelennek meg, és az oldal tetején mindig kiírja a gép aktuális statisztikáit.

Ha hiba volt vele milyen hibák voltak vele: Az első verziónál az AI csak a márkát (pl. BMW) tudta. Emiatt egy olcsóbb 3-as BMW-t és egy drága X5-öst is hasonlóan árazott be, ami nagyon rontotta a pontosságot. A weboldalon pedig nem volt egyértelmű a felhasználónak, hogy a gép mennyit tévedhet.

Mivel javítottam ki a hibákat: Beleraktam a tanuló scriptbe a "modell" oszlopot is. Hogy a weboldalon a felhasználó ne tudjon hülyeséget beírni, írtam egy kis JavaScript (AJAX) kódot, ami a háttérből automatikusan lekéri, hogy a kiválasztott márkához milyen modellek léteznek nálunk. Végül csináltam egy figyelmeztető dobozt a felületre, ami mindig kiírja az AI aktuális pontosságát és átlagos tévedését, ezzel is növelve az átláthatóságot.

## Frontend UI/UX okosítása és a Dinamikus Űrlap

Mit fejlesztettem: A weboldal végleges, letisztult kinézetét (Bootstrap segítségével), és egy 3 lépcsős, okos legördülő menüt (Márka -> Modell -> Üzemanyag). Ehhez a JavaScript logikát kiszerveztem egy külön fájlba, hogy a HTML kód tiszta maradjon.

Ha működött és van eredménye milyen lett: Egy teljesen profi, piacképes felületet kaptam. A felhasználó nem tud érvénytelen adatot megadni, mert a menük egymásra épülnek (ha kiválaszt egy márkát, csak a hozzá tartozó modellek jelennek meg). Az oldal tetején pedig büszkén virít a gép pontossága és átlagos tévedése.

Ha hiba volt vele milyen hibák voltak vele: Amikor a JavaScriptet kiszerveztem egy külön predictor.js fájlba, a weboldal "szétesett", a legördülők nem működtek. A böngésző fejlesztői konzoljában egy piros "404 Not Found" hiba jelent meg, a kód egyszerűen nem találta a fájlt.

Mivel javítottam ki a hibákat: Meg kellett tanulnom a Django statikus fájlkezelési logikáját. Rájöttem, hogy a szerver biztonsági okokból szigorúan szétválasztja a "kiszámolt" HTML-t és a "statikus" fájlokat (JS, CSS). Létrehoztam a megfelelő static/js mappaszerkezetet, beállítottam a settings.py-ban a hivatkozásokat, és egy hard refresh (böngésző gyorsítótár ürítése) után azonnal életre kelt a rendszer.

## Adathiányok kezelése és "Fallback" (tartalék) logika az űrlapon

Mit fejlesztettem: A dinamikus legördülő menük (Márka -> Modell -> Üzemanyag) megbízhatóságát, hogy sose fagyjon meg a folyamat hiányos adatok miatt.

Ha működött és van eredménye milyen lett: A felhasználó sosem akad el az űrlapon. Ha a rendszer ismer minden adatot a modellről, akkor pontosan szűri az üzemanyagokat (pl. Teslánál csak Elektromos). Ha viszont hiányos az adatbázis egy adott típusnál, akkor is felkínálja a leggyakoribb opciókat, így a becslés mindig sikeresen elindítható.

Ha hiba volt vele milyen hibák voltak vele: Tesztelés közben észrevettem, hogy a webről lekapart hirdetéseknél bizonyos ritkább márka-modell kombinációknál egyszerűen hiányzott az üzemanyag típusa az adatok közül. Emiatt a weboldalon, ha a felhasználó kiválasztotta ezt az autót, az üzemanyag legördülő menü teljesen üres maradt, a program "megakadt", és az űrlapot nem lehetett elküldeni.

Mivel javítottam ki a hibákat: Írtam egy úgynevezett "tartalék" (fallback) logikát a backendbe (a Django views.py fájlba). Ha a rendszer az adatbázis szűrése után azt látja, hogy az adott autóhoz nincs egyetlen eltárolt üzemanyagtípus sem, akkor nem ad vissza üres listát. Helyette automatikusan beölti a négy legrelevánsabb, alapértelmezett értéket (Benzin, Dízel, Hibrid, Elektromos).

Vezérlőpult (Admin Dashboard) és Folyamatautomatizálás

Mit fejlesztettem: Egy zárt, csak hitelesített felhasználók (adminok) számára elérhető Vezérlőpultot, ami egyetlen felületen vizualizálja a rendszer állapotát (autók száma, AI pontossága és frissessége, valamint a Scraper futási naplója). Emellett a kód szintjén finomítottam az adatgyűjtő és a tanító algoritmus kapcsolatát.

Ha működött és van eredménye milyen lett: A rendszer üzemeltetőjeként nem kell többé az adatbázisban vagy a terminálban kutakodnom. Egy letisztult, kártyás/táblázatos weblapon azonnal látom a gép működését. A biztonság is garantált, hiszen a felületet csak belépés után lehet elérni. Az adatbázisba pedig hajszálpontos adatok (tényleges darabszámok és befejezési idők) kerülnek.

Ha hiba volt vele milyen hibák voltak vele: Az első verziónál bárki elérhette a statisztikákat a weben. A felület dizájnja (UX/UI) nem volt tökéletes: a hosszú hibaüzenetek (pl. Timeout logok) szétfeszítették a táblázatot, a kártyák aszimmetrikusak voltak, és a scraper manuális számolása (szamlalo += 1) miatt előfordultak pontatlanságok az elmentett darabszámokban.

Mivel javítottam ki a hibákat: A Django beépített @staff_member_required dekorátorával "lezártam" a felületet az illetéktelenek elől. A frontend oldalon a hosszú szövegeket truncatechars szűrővel vágtam le úgy, hogy egérhúzásra azért olvashatóak maradjanak, és egységesítettem a kártyák magasságát. A backendben pedig a manuális számlálót lecseréltem az adatbázis stabil .count() lekérdezésére, és bevezettem a timezone.now() használatát a pontos időbélyegekhez.

## Chrome profil automatizálása és önfrissítő mechanizmusa

Mit fejlesztettem: Továbbfejlesztettem a böngészőprofilt kezelő kódot, hogy teljesen emberi beavatkozás nélkül építse fel a profilt, majd minden adatgyűjtés előtt automatikusan törölje a régit és generáljon egy vadonatújat.

Ha működött és van eredménye milyen lett: A scraper most már önállóan megnyitja a böngészőt, megoldja a Captchát, automatikusan rákattint a süti (cookie) elfogadó gombra, elindít egy keresést, és ha betöltött a találati lista, már kezdi is a munkát. Mivel minden adatgyűjtés előtt tiszta lappal (új profillal) indul, a rendszer folyamatosan védve van a kitiltások ellen.

Ha hiba volt vele milyen hibák voltak vele: Korábban a Chrome profilt és a sütik elfogadását nem tudta önállóan megcsinálni a gép. Ráadásul a Használtautó.hu botvédelme (Cloudflare) idővel felismerte a többször használt böngésző ujjlenyomatát, és véglegesen blokkolta (kitiltotta) a régi profilt, ami miatt a scraper rendre leállt.

Mivel javítottam ki a hibákat: Beépítettem a Python `shutil` modulját, ami a futás legelején kíméletlenül letörli a korábbi profil mappáját. Ezután a Playwright segítségével írtam egy automatizált "setup" fázist, ami egy folyamatos (bezárás nélküli) munkameneten belül megnyitja az oldalt, elfogadja a sütiket, és utána egyből átadja a nyitott böngészőt az adatgyűjtő ciklusnak.

## Botvédelem (Cloudflare) kijátszása és a tempó optimalizálása

Mit fejlesztettem: Finomhangoltam a scraper sebességét és a hálózati forgalom (képek, reklámok) kezelését, hogy "emberibb" viselkedést szimuláljak, és elkerüljem a Cloudflare detektáló rendszereit.

Ha működött és van eredménye milyen lett: A robot stabilan fut több száz oldalon keresztül anélkül, hogy gyanússá válna a szerver számára, a letiltások és a csendes fagyások pedig megszűntek.

Ha hiba volt vele milyen hibák voltak vele: Két komoly probléma is fellépett. Egyrészt az elején bevezetett AdBlocker (képek és média tiltása) miatt az automatizált profilépítés során a weblap sokszor be sem töltött. Másrészt, amikor végre elindult a keresés, a gép olyan irreálisan gyorsan lapozott le egy teljes oldalt, hogy a Cloudflare azonnal botnak nézte, és másodpercek alatt letiltotta a profilt.

Mivel javítottam ki a hibákat: Rájöttem, hogy ha agresszíven blokkolom a képeket, az a Cloudflare számára egyértelmű "nem emberi" viselkedésnek tűnik. Így teljesen kivettem a képek blokkolását a fő folyamatból – a gép enélkül is elég gyorsan szedi az adatokat. A túl gyors lapozás problémáját pedig egy beépített 2 másodperces várakozással (`time.sleep(2)`) oldottam meg minden oldalozásnál, így a kérések tempója életszerűbbé vált a szerver felé.

# Projekt készen áll...