
import os
import joblib
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from .models import Ad, AILog

# --- EZ FELEL A DINAMIKUS LEGÖRDÜLŐÉRT ---
def get_models(request):
    brand = request.GET.get('brand')
    if brand:
        # Lekérjük az adott márkához tartozó egyedi modelleket
        models = Ad.objects.filter(brand=brand).exclude(model="").values_list('model', flat=True).distinct().order_by('model')
        return JsonResponse(list(models), safe=False)
    return JsonResponse([], safe=False)

# --- EZ FELEL AZ ÁRBECSLÉSÉRT ---
def price_predictor(request):
    prediction = None
    error_msg = None
    
    latest_ai_stat = AILog.objects.first()
    ai_accuracy_percent = latest_ai_stat.r2_score * 100

    brands = Ad.objects.exclude(brand="").values_list('brand', flat=True).distinct().order_by('brand')
    fuels = Ad.objects.exclude(fuel="").values_list('fuel', flat=True).distinct().order_by('fuel')

    model_path = os.path.join(settings.BASE_DIR, 'ai', 'models', 'car_price_predictor.pkl')
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        model = None
        error_msg = "Az AI modell nem található! Futtasd le a tanító scriptet."

    if request.method == 'POST' and model:
        try:
            # --- ITT KERÜL BE A 'model' A PANDAS TÁBLÁBA ---
            input_data = pd.DataFrame([{
                'brand': request.POST.get('brand'),
                'model': request.POST.get('model'), # Ez hiányzott korábban!
                'year': int(request.POST.get('year', 2015)),
                'fuel': request.POST.get('fuel'),
                'engine_cc': int(request.POST.get('engine_cc', 1500)),
                'power_le': int(request.POST.get('power_le', 100)),
                'mileage': int(request.POST.get('mileage', 150000))
            }])

            pred_value = model.predict(input_data)[0]
            prediction = f"{int(pred_value):,} Ft".replace(',', ' ')
            
        except Exception as e:
            error_msg = f"Hiba történt a becslés során: {str(e)}"

    context = {
        'prediction': prediction,
        'error_msg': error_msg,
        'brands': brands,
        'fuels': fuels,
        'ai_stat': latest_ai_stat,
        'ai_accuracy_percent': ai_accuracy_percent,
    }
    
    return render(request, 'ads/predictor.html', context)
