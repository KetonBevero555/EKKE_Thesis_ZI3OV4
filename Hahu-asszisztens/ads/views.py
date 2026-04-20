
import os
import joblib
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from .models import Ad, AILog, ScrapeLog, DummyAd
from django.contrib.admin.views.decorators import staff_member_required

# Keresés segítő, hogy a legördülőlistában csak valódi üzemanyag típusok jelenjenek meg
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
def get_models(request):
    brand = request.GET.get('brand')
    if brand:
        models = Ad.objects.filter(brand=brand).exclude(model="").values_list('model', flat=True).distinct().order_by('model')
        return JsonResponse(list(models), safe=False)
    return JsonResponse([], safe=False)

# Kommunikáció a frontenddel - Ő adja a paramétereket és kapja vissza a becslést - Ő felel a tájéokztatásért is az MI pontosságáról
def price_predictor(request):
    prediction = None
    error_msg = None
    
    latest_ai_stat = AILog.objects.first()
    ai_accuracy_percent = latest_ai_stat.r2_score * 100 if latest_ai_stat and latest_ai_stat.r2_score else 0

    brands = Ad.objects.exclude(brand="").values_list('brand', flat=True).distinct().order_by('brand')
    fuels = Ad.objects.exclude(fuel="").values_list('fuel', flat=True).distinct().order_by('fuel')

    model_path = os.path.join(settings.BASE_DIR, 'ai', 'models', 'car_price_predictor.pkl')
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        model = None
        error_msg = "Az MI modell nem található!"

    if request.method == 'POST' and model:
        try:
            input_data = pd.DataFrame([{
                'brand': request.POST.get('brand'),
                'model': request.POST.get('model'),
                'year': int(request.POST.get('year', 2015)),
                'fuel': request.POST.get('fuel'),
                'engine_cc': int(request.POST.get('engine_cc', 1500)),
                'power_le': int(request.POST.get('power_le', 100)),
                'mileage': int(request.POST.get('mileage', 100000))
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

@staff_member_required
def dashboard(request):
    total_ads = Ad.objects.count()
    total_dummy = DummyAd.objects.count()
    latest_ai = AILog.objects.first()
    ai_accuracy_percent = latest_ai.r2_score * 100 if latest_ai and latest_ai.r2_score else 0
    recent_scrapes = ScrapeLog.objects.order_by('-start_time')[:20]

    context = {
        'total_ads': total_ads,
        'total_dummy': total_dummy,
        'latest_ai': latest_ai,
        'recent_scrapes': recent_scrapes,
        'ai_accuracy_percent': ai_accuracy_percent,
    }
    return render(request, 'ads/dashboard.html', context)
