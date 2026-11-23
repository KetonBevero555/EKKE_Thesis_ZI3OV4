import os
import sys
import django
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_absolute_percentage_error
from catboost import CatBoostRegressor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hahu_backend.settings')
django.setup()

from ads.models import Ad

def run_evaluation():
    print("Loading data from the database...")
    qs = Ad.objects.all().values('hahu_id', 'brand', 'model', 'fuel', 'year', 'mileage', 'power_le', 'price')
    df = pd.DataFrame(list(qs))
    print(f"Initial record count: {len(df)}")

    df = df.dropna(subset=['price', 'year', 'mileage', 'power_le'])
    df = df[(df['price'] >= 200000) & (df['price'] <= 50000000)]

    categorical_features = ['brand', 'model', 'fuel']
    numeric_features = ['year', 'mileage', 'power_le']

    for col in categorical_features:
        df[col] = df[col].fillna('Unknown').astype(str)

    # Duplikációk eltávolítása
    df = df.drop_duplicates(subset=['hahu_id'])
    df = df.drop_duplicates(subset=categorical_features + numeric_features + ['price'])
    print(f"Cleaned, deduplicated record count: {len(df)}\n")

    X = df[categorical_features + numeric_features]
    y = df['price'].values

    SEEDS = [15, 42, 100, 123, 456, 777, 1337, 2020, 3773, 5555]

    rf_metrics = {'mae': [], 'mape': [], 'r2': []}
    cb_metrics = {'mae': [], 'mape': [], 'r2': []}

    for i, seed in enumerate(SEEDS, 1):
        print(f"=== Run {i}/{len(SEEDS)} (random_seed={seed}) ===")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)

        # --- Random Forest ---
        preprocessor = ColumnTransformer(transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
        rf_model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', TransformedTargetRegressor(
                regressor=RandomForestRegressor(n_estimators=300, random_state=seed, n_jobs=-1),
                func=np.log1p,
                inverse_func=np.expm1
            ))
        ])
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)

        rf_mae = mean_absolute_error(y_test, rf_pred)
        rf_mape = mean_absolute_percentage_error(y_test, rf_pred) * 100
        rf_r2 = r2_score(y_test, rf_pred)
        rf_metrics['mae'].append(rf_mae)
        rf_metrics['mape'].append(rf_mape)
        rf_metrics['r2'].append(rf_r2)
        print(f"  [RF] MAE: {rf_mae:,.0f} HUF | MAPE: {rf_mape:.2f}% | R2: {rf_r2:.4f}")

        # --- CatBoost ---
        cb_model = CatBoostRegressor(
            iterations=10000,
            learning_rate=0.1,
            depth=10,
            cat_features=categorical_features,
            verbose=0,
            random_seed=seed
        )
        cb_model.fit(X_train, np.log1p(y_train))
        cb_pred = np.expm1(cb_model.predict(X_test))

        cb_mae = mean_absolute_error(y_test, cb_pred)
        cb_mape = mean_absolute_percentage_error(y_test, cb_pred) * 100
        cb_r2 = r2_score(y_test, cb_pred)
        cb_metrics['mae'].append(cb_mae)
        cb_metrics['mape'].append(cb_mape)
        cb_metrics['r2'].append(cb_r2)
        print(f"  [CB] MAE: {cb_mae:,.0f} HUF | MAPE: {cb_mape:.2f}% | R2: {cb_r2:.4f}\n")

    print("================ FINAL RESULTS (MEAN ± STD) ================")
    for name, m in [("Random Forest", rf_metrics), ("CatBoost", cb_metrics)]:
        print(f"{name}:")
        print(f"  MAE:  {np.mean(m['mae']):,.0f} ± {np.std(m['mae']):,.0f} HUF")
        print(f"  MAPE: {np.mean(m['mape']):.2f} ± {np.std(m['mape']):.2f} %")
        print(f"  R²:   {np.mean(m['r2']):.4f} ± {np.std(m['r2']):.4f}")

if __name__ == '__main__':
    run_evaluation()
