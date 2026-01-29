from django.db import models
from django.contrib.auth.models import User

class BaseAd(models.Model):
    # Hirdetés azonosító és URL mezői
    hahu_id = models.IntegerField(unique=True)
    url = models.URLField(max_length=500)

    # Jármű alapvető mezői
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    title = models.CharField(max_length=300)

    # Jármű árának mezői
    price = models.IntegerField(null=True, blank=True)
    sale_price = models.IntegerField(null=True, blank=True)
    no_price = models.BooleanField(default=False)
    is_rentable = models.BooleanField(default=False)

    # Jármű adatainak mezői
    fuel = models.CharField(max_length=50, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    engine_cc = models.IntegerField(null=True, blank=True)
    power_le = models.IntegerField(null=True, blank=True)
    power_kw = models.IntegerField(null=True, blank=True)
    mileage = models.IntegerField(null=True, blank=True)

    # Egyéb mezők
    tags = models.TextField(blank=True)
    description_snippet = models.TextField(blank=True)
    seller = models.CharField(max_length=200, null=True, blank=True)

    # Létrehozás dátuma
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class Ad(BaseAd):
    # Felhasználók, akik kedvelték a hirdetést
    favorited_by = models.ManyToManyField(User, related_name='favorite_ads', blank=True)

    class Meta:
        db_table = 'ads'

class DummyAd(BaseAd):
    class Meta:
        db_table = 'dummy_ads'

class ScrapeLog(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    expected_cars = models.IntegerField()
    actual_scraped = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='PENDING')

    class Meta:
        db_table = 'scrape_logs'
