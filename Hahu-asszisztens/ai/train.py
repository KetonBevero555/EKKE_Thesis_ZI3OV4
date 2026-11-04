import os
import sys
import django
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.compose import TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hahu_backend.settings')
django.setup()

from ads.models import Ad, AILog

def train_model_random_forest():
    print("\n<RFM> Starting (Random Forest) model training process...")

    print("<RFM> Loading data from database...")
    qs = Ad.objects.filter(
        price__isnull=False,
        year__isnull=False,
        mileage__isnull=False,
        power_le__isnull=False
    ).values('price', 'brand', 'model', 'year', 'fuel',
             #'engine_cc', # <- Kommentelve, mert az új Hahu oldal nem tartalmazza
             'power_le', 'mileage')

    df = pd.DataFrame.from_records(qs)
    print(f"<RFM> Loaded number of cars: {len(df)} cars")

    print("<RFM> Preparing data and filtering outliers...")
    df = df[(df['price'] >= 200_000) & (df['price'] <= 50_000_000)]
    
    X = df.drop('price', axis=1)
    y = df['price']
    
    categorical_features = ['brand', 'model', 'fuel']
    numeric_features = ['year',
                        #'engine_cc', # <- Kommentelve
                        'power_le', 'mileage']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Logaritmikus pipeline
    base_regressor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', TransformedTargetRegressor(
            regressor=base_regressor,
            func=np.log1p,         # Tanításkor logaritmust von az árból
            inverse_func=np.expm1  # Becsléskor visszaváltja Forintra
        ))
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("<RFM> Training model...")
    model.fit(X_train, y_train)

    print("<RFM> Testing model...")
    # A predict forintot ad vissza.
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\n=========== RF MODEL ACCURACY ===========")
    print(f"Average mistake (MAE): {mae:,.0f} Ft")
    print(f"Model accuracy (R2 Score): {100*r2:.2f} %")
    print("===========================================\n")

    print("<RFM> Saving model and logs...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(current_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'RF_model.pkl')
    joblib.dump(model, model_path)
    
    print(f"<RFM> Training completed. Model saved to: {model_path}")
    
    AILog.objects.create(mae=mae, r2_score=r2)
    print("<RFM> Log finalized to AILog datatable.")


from catboost import CatBoostRegressor

def train_model_catboost():
    print("\n<CBM> Starting (CatBoost) model training process...")

    print("<CBM> Loading data from database...")
    qs = Ad.objects.filter(
            price__isnull=False,
            year__isnull=False,
            mileage__isnull=False,
            power_le__isnull=False
        ).values('price', 'brand', 'model', 'year', 'fuel',
                 #'engine_cc', # <- Kommentelve, mert az új Hahu oldal nem tartalmazza
                 'power_le', 'mileage')
    
    df = pd.DataFrame.from_records(qs)
    print(f"<CBM> Loaded number of cars: {len(df)} cars")

    print("<CBM> Preparing data and filtering outliers...")
    df = df[(df['price'] >= 200_000) & (df['price'] <= 50_000_000)]
    
    # Hiányzó szöveges adatok tisztítása
    categorical_features = ['brand', 'model', 'fuel']
    for col in categorical_features:
        df[col] = df[col].fillna('Unknown').astype(str)
        
    X = df.drop('price', axis=1)
    y = np.log1p(df['price'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("<CBM> Training CatBoost model...")
    model = CatBoostRegressor(
        iterations=10000, 
        learning_rate=0.1, 
        depth=10, 
        cat_features=categorical_features, 
        verbose=500,
        random_seed=42
    )
    
    model.fit(X_train, y_train)
    
    y_pred_log = model.predict(X_test)
    y_pred = np.expm1(y_pred_log)
    y_test_real = np.expm1(y_test)
    
    global_mae = mean_absolute_error(y_test_real, y_pred)
    global_r2 = r2_score(y_test_real, y_pred)
    
    # Statisztikák
    print('Statistics')
    feature_importances = model.get_feature_importance()
    importance_df = pd.DataFrame({
        'Parameters': X_train.columns,
        'Weight (%)': feature_importances
    }).sort_values(by='Weight (%)', ascending=False)
    print(importance_df.to_string(index=False))
    
    mask_under_5m = y_test_real < 5_000_000
    mask_over_5m = y_test_real >= 5_000_000
    
    if mask_under_5m.any():
        mae_under = mean_absolute_error(y_test_real[mask_under_5m], y_pred[mask_under_5m])
        print(f"MAE below 5 million Ft: {mae_under:,.0f} Ft")
        
    if mask_over_5m.any():
        mae_over = mean_absolute_error(y_test_real[mask_over_5m], y_pred[mask_over_5m])
        print(f"MAE above 5 million Ft: {mae_over:,.0f} Ft")

    # Mentés
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'CB_model.pkl')
    joblib.dump(model, model_path)
    
    AILog.objects.create(mae=global_mae, r2_score=global_r2)
    print(f"<CBM> Model saved: {model_path}")

def train_models():
    train_model_random_forest()
    train_model_catboost()

if __name__ == '__main__':
    train_models()
