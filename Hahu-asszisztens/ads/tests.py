from django.test import TestCase, Client
from django.contrib.auth.models import User
from ads.models import Ad

class HahuAsszisztensTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.guest_user = User.objects.create_user(username='guest', password='testpassword')
        self.staff_user = User.objects.create_user(username='admin', password='adminpassword', is_staff=True)

        Ad.objects.create(
            hahu_id=99999999,
            brand='Ford',
            model='Focus',
            fuel='Benzin',
            price=2500000,
            year=2015,
            engine_cc=2000,
            power_le=150,
            mileage=50000
        )

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
        self.assertIn('error_msg', response.context)
        self.assertContains(response, "Kérjük, töltse ki az összes mezőt érvényes adatokkal!")

    def test_api_get_models_returns_json(self):
        """5. Teszt: Az AJAX végpont helyesen adja vissza egy márka modelljeit"""
        response = self.client.get('/api/get-models/?brand=Ford')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        models_list = data.get('models', []) if isinstance(data, dict) else data
        self.assertIn('Focus', models_list)

    def test_api_get_fuels_returns_json(self):
        """6. Teszt: Az AJAX végpont helyesen adja vissza egy autó üzemanyagtípusait"""
        response = self.client.get('/api/get-fuels/?brand=Ford&model=Focus')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        fuels_list = data.get('fuels', []) if isinstance(data, dict) else data
        self.assertIn('Benzin', fuels_list)

    def test_post_invalid_year_handling(self):
        """7. Teszt: POST kérés kezelése a szerveren. (Érvénytelen évjárat)"""
        response = self.client.post('/', {
            'brand': 'Ford',
            'model': 'Focus',
            'fuel': 'Benzin',
            'year': '2050', #<- Érvénytelen évjárat
            'mileage': '50000',
            'engine_cc': '2200',
            'power_le': '150'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('error_msg', response.context)
        self.assertContains(response, 'Az évjáratnak 1880')

    def test_post_invalid_mileage_handling(self):
        """8. Teszt: POST kérés kezelése a szerveren. (Érvénytelen futásteljesítmény)"""
        response = self.client.post('/', {
            'brand': 'Ford',
            'model': 'Focus',
            'fuel': 'Benzin',
            'year': '2015',
            'mileage': '-50000', #<- Érvénytelen futásteljesítmény
            'engine_cc': '2200',
            'power_le': '150'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('error_msg', response.context)
        self.assertContains(response, 'A futásteljesítmény')

    def test_post_invalid_power_le_handling(self):
        """9. Teszt: POST kérés kezelése a szerveren. (Érvénytelen teljesítmény)"""
        response = self.client.post('/', {
            'brand': 'Ford',
            'model': 'Focus',
            'fuel': 'Benzin',
            'year': '2015',
            'mileage': '50000',
            'engine_cc': '2200',
            'power_le': '5' #<- Érvénytelen teljesítmény
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('error_msg', response.context)
        self.assertContains(response, 'A teljesítménynek legalább')

#    def test_post_invalid_engine_cc_handling(self):
#        """10. Teszt: POST kérés kezelése a szerveren. (Érvénytelen hengerűrtartalom)"""
#        response = self.client.post('/', {
#            'brand': 'Ford',
#            'model': 'Focus',
#            'fuel': 'Benzin',
#            'year': '2015',
#            'mileage': '50000',
#            'engine_cc': '400', #<- Érvénytelen hengerűrtartalom
#            'power_le': '150'
#        })
#        self.assertEqual(response.status_code, 200)
#        self.assertIn('error_msg', response.context)
#        self.assertContains(response, 'A hengerűrtartalom legalább')
