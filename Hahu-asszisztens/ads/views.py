
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

# Kommunikáció a frontenddel - Ő adja a paramétereket és kapja vissza a becslést - Ő felel a tájéokztatásért is az MI pontosságáról
def price_predictor(request):
    if request.method == 'POST':
        try:
            brand = request.POST.get('brand') # in Ad.brand
            model = request.POST.get('model') # in Ad.model
            fuel = request.POST.get('fuel') # in Ad.fuel
            milage = int(request.POST.get('mileage')) # min 0
            #engine_cc = int(request.POST.get('engine_cc')) # min 500 # <- Kommentelve, mert az új Hahu oldal nem tartalmazza
            power_le = int(request.POST.get('power_le')) # min 10

            year = int(request.POST.get('year'))
            current_year = datetime.date.today().year
            
            if year > current_year or year < 1880:
                return render(request, 'ads/predictor.html', {
                    'error': f'Az évjáratnak 1880 és {current_year} között kell lennie!'
                })
                
        except (ValueError, TypeError):
            return render(request, 'ads/predictor.html', {
                'error': 'Kérjük, töltse ki az összes numerikus mezőt érvényes adatokkal!'
            })

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
                #'engine_cc': int(request.POST.get('engine_cc', 1500)), # <- Kommentelve, mert az új Hahu oldal nem tartalmazza
                'power_le': int(request.POST.get('power_le', 100)),
                'mileage': int(request.POST.get('mileage', 100000))
            }])

            pred_value = model.predict(input_data)[0]
            prediction = f"{round(int(pred_value), -3):,} Ft".replace(',', ' ')
            
        except Exception as e:
            error_msg = f"Hiba történt a becslés során: {str(e)}"

    context = {
        'prediction': prediction,
        'error_msg': error_msg,
        'brands': brands,
        'fuels': fuels,
        'ai_stat': latest_ai_stat,
        'ai_accuracy_percent': ai_accuracy_percent,
        'form_data': request.POST if request.method == 'POST' else None,
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

    context = {
        'total_ads': total_ads,
        'total_dummy': total_dummy,
        'latest_ai': latest_ai,
        'recent_scrapes': recent_scrapes,
        'ai_accuracy_percent': ai_accuracy_percent,
    }
    return render(request, 'ads/dashboard.html', context)
