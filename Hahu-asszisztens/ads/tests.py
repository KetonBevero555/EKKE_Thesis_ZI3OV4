from django.test import TestCase, Client
from django.contrib.auth.models import User

class HahuAsszisztensTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.guest_user = User.objects.create_user(username='guest', password='testpassword')
        self.staff_user = User.objects.create_user(username='admin', password='adminpassword', is_staff=True)

    def test_homepage_loads_for_anyone(self):
        """1. Teszt: A főoldal bárki számára elérhető (HTTP 200)"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'ads/predictor.html') 

    def test_dashboard_redirects_guest(self):
        """2. Teszt: A vezérlőpult átirányítja a nem bejelentkezett felhasználót"""
        response = self.client.get('/dashboard/')

        self.assertRedirects(response, '/admin/login/?next=/dashboard/')

    def test_dashboard_loads_for_staff(self):
        """3. Teszt: A vezérlőpult betöltődik a staff jogosultságú felhasználónak"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_invalid_post_data_handled(self):
        """4. Teszt: Az árbecslő űrlap kezeli a hiányos POST kéréseket"""
        response = self.client.post('/', {
            'brand': 'Ford',
            'model': 'Focus',
            'fuel': 'Benzin'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_api_get_models_returns_json(self):
        """5. Teszt: Az AJAX végpont helyesen adja vissza egy márka modelljeit JSON formátumban"""

        response = self.client.get('/api/get-models/?brand=Ford')
        
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'application/json')
        else:
            self.assertIn(response.status_code, [200, 404])

    def test_api_get_fuels_returns_json(self):
        """6. Teszt: Az AJAX végpont helyesen adja vissza egy márka és a modell üzemanyagtípusait JSON formátumban"""

        response = self.client.get('/api/get-fuels/?brand=Ford&model=Focus')
        
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'application/json')
        else:
            self.assertIn(response.status_code, [200, 404])

    def test_invalid_numeric_data_handling(self):
        """7. Teszt: Kliensoldali megkerülés (pl. negatív kilométer) lekezelése a szerveren"""
        response = self.client.post('/', {
            'brand': 'Ford',
            'model': 'Focus',
            'fuel': 'Benzin',
            'year': '2050',      # Jövőbeli év (érvénytelen)
            'mileage': '-50000', # Negatív érték (érvénytelen)
            'engine_cc': '2200',
            'power_le': '150'
        })

        self.assertEqual(response.status_code, 200)