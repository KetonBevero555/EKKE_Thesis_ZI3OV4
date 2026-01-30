import os
import time
from seleniumbase import sb_cdp

def setup_profile():
    # 1. Meghatározzuk a profil mappa helyét a projekten belül
    # Ez a "hahu_backend/ads/chrome_profile" mappa lesz
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "chrome_profile")
    
    print(f"Profil mappa létrehozása/betöltése itt: {profile_dir}")
    print("A böngésző meg fog nyílni.")
    print("TEENDŐD: 1. Fogadd el a sütiket. 2. Oldd meg a Captchát. 3. ZÁRD BE a böngészőt kézzel, ha végeztél!")

    # 2. Megnyitjuk a Chrome-ot ezzel a profillal
    sb = sb_cdp.Chrome(
        user_data_dir=profile_dir,  # <--- ITT A LÉNYEG: Ebbe a mappába ment mindent
        incognito=False             # Fontos! NEM lehet inkognitó, mert menteni akarunk
    )
    
    endpoint = sb.get_endpoint_url()
    print(f"Böngésző fut. Endpoint: {endpoint}")
    
    # Itt csak várunk a végtelenségig, amíg te be nem zárod az ablakot
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Leállítás...")

if __name__ == "__main__":
    setup_profile()
    