import os
import sys
import django
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# --- DJANGO KÖRNYEZET BETÖLTÉSE ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hahu_backend.settings')
django.setup()

from ads.models import Ad

def train_model():
    print("1. Adatok betöltése az adatbázisból...")
    
    # Csak azokat az autókat kérjük le, ahol megvannak a legfontosabb adatok
    qs = Ad.objects.filter(
        price__isnull=False,
        year__isnull=False,
        mileage__isnull=False,
        power_le__isnull=False
    ).values('price', 'brand', 'year', 'fuel', 'engine_cc', 'power_le', 'mileage')

    df = pd.DataFrame.from_records(qs)
    print(f"Betöltött autók száma: {len(df)} db")

    # --- ADATTISZTÍTÁS (Data Cleaning) ---
    print("2. Adatok tisztítása...")
    # Kiszűrjük az irreális árakat (pl. 100 forintos hibás hirdetések, vagy 1 milliárdosok)
    df = df[(df['price'] > 200000) & (df['price'] < 100000000)]
    
    # Ha hiányzik a köbcenti, kitöltjük a mediánnal (középső érték), hogy ne omoljon össze az AI
    df['engine_cc'] = df['engine_cc'].fillna(df['engine_cc'].median())

    # --- BEMENET ÉS CÉL MEGHATÁROZÁSA ---
    print("3. Adatok előkészítése a tanításhoz...")
    X = df.drop('price', axis=1) # Bemeneti adatok (Tulajdonságok)
    y = df['price']              # Cél változó (Amit be akarunk csülni)

    # Az AI csak számokat ért, ezért a szövegeket (Márka, Üzemanyag) át kell alakítani (One-Hot Encoding)
    categorical_features = ['brand', 'fuel']
    numeric_features = ['year', 'engine_cc', 'power_le', 'mileage']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # --- A MODELL FELÉPÍTÉSE ---
    # Random Forest algoritmust használunk 100 döntési fával (n_estimators=100)
    # n_jobs=-1 azt jelenti, hogy a processzorod összes magját használja, hogy gyorsabb legyen
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))
    ])

    # --- TESZT KÖRNYEZET KIALAKÍTÁSA ---
    # Az adatok 80%-án tanítjuk a modellt, 20%-án pedig leteszteljük, hogy nem csak "biflázott-e"
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- TANÍTÁS ---
    print("AI Tanítása (Ez eltarthat 1-2 percig a gépeden)...")
    model.fit(X_train, y_train)

    # --- KIÉRTÉKELÉS ---
    print("Modell tesztelése...")
    y_pred = model.predict(X_test) # Megkérjük, hogy becsülje meg a teszt autók árát
    
    # Kiszámoljuk a hibát
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\n============ EREDMÉNYEK ============")
    print(f"Átlagos tévedés (MAE): {mae:,.0f} Ft")
    print(f"Modell pontossága (R2 Score): {r2:.2f}")
    print("======================================\n")

    # --- MENTÉS ---
    print("6. Modell elmentése későbbi használatra...")
    
    # Megkeressük, hol van ez a train.py fájl pontosan (abszolút útvonal)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ezen belül hozzuk létre a models mappát
    models_dir = os.path.join(current_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Ide mentjük a fájlt
    model_path = os.path.join(models_dir, 'car_price_predictor.pkl')
    joblib.dump(model, model_path)
    
    print(f"✅ Minden kész! A modell ide lett mentve: {model_path}")

if __name__ == '__main__':
    train_model()