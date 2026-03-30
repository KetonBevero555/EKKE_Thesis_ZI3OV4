
import os
import joblib
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from .models import Ad

def price_predictor(request):
    prediction = None
    error_msg = None
    
    # 1. Elérhető márkák és üzemanyagok lekérdezése az adatbázisból a legördülő menükhöz
    # (Így a felhasználó csak olyan márkát választhat, ami létezik is nálunk)
    brands = Ad.objects.exclude(brand="").values_list('brand', flat=True).distinct().order_by('brand')
    fuels = Ad.objects.exclude(fuel="").values_list('fuel', flat=True).distinct().order_by('fuel')

    # 2. AI Modell betöltése
    # A settings.BASE_DIR a 'Hahu-asszisztens' gyökérkönyvtára
    model_path = os.path.join(settings.BASE_DIR, 'ai', 'models', 'car_price_predictor.pkl')
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        model = None
        error_msg = "Az AI modell nem található! Futtasd le a tanító scriptet."

    # 3. Ha a felhasználó rányomott a "Becslés" gombra (POST kérés)
    if request.method == 'POST' and model:
        try:
            # Adatok kinyerése az űrlapból
            brand = request.POST.get('brand')
            year = int(request.POST.get('year', 2015))
            fuel = request.POST.get('fuel')
            engine_cc = int(request.POST.get('engine_cc', 1500))
            power_le = int(request.POST.get('power_le', 100))
            mileage = int(request.POST.get('mileage', 150000))

            # A Pandas DataFrame felépítése (pontosan úgy, ahogy tanítottuk)
            input_data = pd.DataFrame([{
                'brand': brand,
                'year': year,
                'fuel': fuel,
                'engine_cc': engine_cc,
                'power_le': power_le,
                'mileage': mileage
            }])

            # AI Becslés futtatása
            pred_value = model.predict(input_data)[0]
            
            # Szépítés: "3 500 000 Ft" formátum
            prediction = f"{int(pred_value):,} Ft".replace(',', ' ')
            
        except Exception as e:
            error_msg = f"Hiba történt a becslés során: {str(e)}"

    # Ezt küldjük ki a HTML oldalnak
    context = {
        'prediction': prediction,
        'error_msg': error_msg,
        'brands': brands,
        'fuels': fuels,
    }
    
    return render(request, 'ads/predictor.html', context)