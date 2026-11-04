
import os
import joblib
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from .models import Ad, AILog, ScrapeLog, DummyAd
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET
import datetime
import numpy as np

# Keresés segítő, hogy a legördülőlistában csak valódi üzemanyag típusok jelenjenek meg
@require_GET
def get_fuels(request):
    brand = request.GET.get('brand')
    model = request.GET.get('model')
    if brand and model:
        fuels = Ad.objects.filter(brand=brand, model=model).exclude(fuel__isnull=True).exclude(fuel="").exclude(fuel="None").values_list('fuel', flat=True).distinct().order_by('fuel')
        if not fuels:
            return JsonResponse(['Benzin', 'Dízel', 'Elektromos', 'Hibrid'], safe=False)
        return JsonResponse(list(fuels), safe=False)
    return JsonResponse([], safe=False)

# Keresés segítő, hogy a legördülőlistában csak valódi modellek jelenjenek meg
@require_GET
def get_models(request):
    brand = request.GET.get('brand')
    if brand:
        models = Ad.objects.filter(brand=brand).exclude(model="").values_list('model', flat=True).distinct().order_by('model')
        return JsonResponse(list(models), safe=False)
    return JsonResponse([], safe=False)

# Kommunikáció a frontenddel - Ő adja a paramétereket és kapja vissza a becslést
def price_predictor(request):
    selected_ai = request.POST.get('ai_type', 'catboost') if request.method == 'POST' else 'catboost'
    prediction = None
    error_msg = None
    
    latest_ai_stat = AILog.objects.first()
    ai_accuracy_percent = latest_ai_stat.r2_score * 100 if latest_ai_stat and latest_ai_stat.r2_score else 0
    brands = Ad.objects.exclude(brand="").values_list('brand', flat=True).distinct().order_by('brand')
    fuels = Ad.objects.exclude(fuel="").values_list('fuel', flat=True).distinct().order_by('fuel')

    # Csak akkor próbálunk becsülni, ha tényleg rányomtak a "Becslés Indítása" gombra (van márka beküldve)
    if request.method == 'POST':
        try:
            brand = request.POST.get('brand')
            model = request.POST.get('model')
            fuel = request.POST.get('fuel')
            milage = int(request.POST.get('mileage'))
            #engine_cc = int(request.POST.get('engine_cc')) # <- Kommentelve, mert az új Hahu oldal nem tartalmazza
            power_le = int(request.POST.get('power_le'))
            year = int(request.POST.get('year'))
            
            current_year = datetime.date.today().year

            # Validációs ellenőrzések
            if year > current_year or year < 1880:
                error_msg = f'Az évjáratnak 1880 és {current_year} között kell lennie!'
            elif milage < 0:
                error_msg = 'A futásteljesítmény nem lehet negatív!'
            elif power_le < 10:
                error_msg = 'A teljesítménynek legalább 10 lóerőnek kell lennie!'
            #elif engine_cc < 500:
                #error_msg = 'A hengerűrtartalom legalább 500 cm³-nek kell lennie!'
            else:
                # MI modell kiválasztása
                model_filename = 'RF_model.pkl' if selected_ai == 'random_forest' else 'CB_model.pkl'
                model_path = os.path.join(settings.BASE_DIR, 'ai', 'models', model_filename)
                
                try:
                    ai_model = joblib.load(model_path)
                    
                    input_data = pd.DataFrame([{
                        'brand': brand, 'model': model, 'year': year,
                        'fuel': fuel, 'power_le': power_le, 'mileage': milage
                    }])

                    raw_prediction = ai_model.predict(input_data)[0]
                    
                    # RF alapból Forintot ad, a CB logaritmust (ezért kell a np.expm1)
                    pred_value = np.expm1(raw_prediction) if selected_ai == 'catboost' else raw_prediction
                    prediction = f"{round(int(pred_value), -3):,} Ft".replace(',', ' ')
                    
                except FileNotFoundError:
                    error_msg = f"Az MI modell ({model_filename}) nem található!"
                except Exception as e:
                    error_msg = f"Hiba történt a becslés során: {str(e)}"
                    
        except (ValueError, TypeError):
            error_msg = 'Kérjük, töltse ki az összes mezőt érvényes adatokkal!'

    # Kontextus átadása egyetlen, biztonságos ponton
    context = {
        'prediction': prediction,
        'error_msg': error_msg,
        'brands': brands,
        'fuels': fuels,
        'ai_stat': latest_ai_stat,
        'ai_accuracy_percent': ai_accuracy_percent,
        'form_data': request.POST if request.method == 'POST' else None,
        'selected_ai': selected_ai,
    }
    
    return render(request, 'ads/predictor.html', context)

@require_GET
@staff_member_required
def dashboard(request):
    total_ads = Ad.objects.count()
    total_dummy = DummyAd.objects.count()
    latest_ai = AILog.objects.first()
    ai_accuracy_percent = latest_ai.r2_score * 100 if latest_ai and latest_ai.r2_score else 0
    recent_scrapes = ScrapeLog.objects.order_by('-start_time')[:20]

    # CatBoost súlyok lekérése és feldolgozása a dashboardhoz
    feature_importances = []
    try:
        cb_model_path = os.path.join(settings.BASE_DIR, 'ai', 'models', 'CB_model.pkl')
        cb_model = joblib.load(cb_model_path)
        
        # Súlyok és nevek lekérése
        importances = cb_model.get_feature_importance()
        feature_names = cb_model.feature_names_
        
        # Párosítás és sorbarendezés csökkenő sorrendben
        fi_list = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
        
        # Színek és fordítások a megjelenítéshez
        colors = ['primary', 'info', 'warning', 'danger', 'success', 'secondary']
        translations = {
            'year': 'Évjárat (Year)',
            'power_le': 'Teljesítmény (LE)',
            'mileage': 'Futásteljesítmény (Km)',
            'brand': 'Márka (Brand)',
            'model': 'Modell (Model)',
            'fuel': 'Üzemanyag (Fuel)'
        }
        
        # Csak a top 4 értéket küldjük át a dizájn miatt
        for i, (feat, imp) in enumerate(fi_list):
            feature_importances.append({
                'name': translations.get(feat, feat),
                'value': round(imp, 1),
                'color': colors[i % len(colors)]
            })
    except Exception as e:
        print(f"Nem sikerült betölteni a CB modellt a súlyokhoz: {e}")

    context = {
        'total_ads': total_ads,
        'total_dummy': total_dummy,
        'latest_ai': latest_ai,
        'recent_scrapes': recent_scrapes,
        'ai_accuracy_percent': ai_accuracy_percent,
        'feature_importances': feature_importances,
    }
    return render(request, 'ads/dashboard.html', context)
