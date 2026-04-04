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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hahu_backend.settings')
django.setup()

from ads.models import Ad, AILog

def train_model():
    print("\n<M> Starting training process...")

    print("<M> Loading data from database...")
    qs = Ad.objects.filter(
        price__isnull=False,
        year__isnull=False,
        mileage__isnull=False,
        power_le__isnull=False
    ).values('price', 'brand', 'model', 'year', 'fuel', 'engine_cc', 'power_le', 'mileage')

    df = pd.DataFrame.from_records(qs)
    print(f"<M> Loaded number of cars: {len(df)} cars")

    print("<M> Preparing data...")
    df = df[(df['price'] > 200000) & (df['price'] < 100000000)]
    df['engine_cc'] = df['engine_cc'].fillna(df['engine_cc'].median())
    X = df.drop('price', axis=1)
    y = df['price']
    
    categorical_features = ['brand', 'model', 'fuel']
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
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("<M> Training model...")
    model.fit(X_train, y_train)

    print("<M> Testing model...")
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\n============ EREDMÉNYEK ============")
    print(f"Average mistake (MAE): {mae:,.0f} Ft")
    print(f"Model accuracy (R2 Score): {100*r2:.2f} %")
    print("======================================\n")

    print("<M> Saving model and logs...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(current_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'car_price_predictor.pkl')
    joblib.dump(model, model_path)
    
    print(f"<M> Training completed. Model saved to: {model_path}")
    
    AILog.objects.create(mae=mae, r2_score=r2)
    print("<M> Log saved to AILog datatable.")

if __name__ == '__main__':
    train_model()