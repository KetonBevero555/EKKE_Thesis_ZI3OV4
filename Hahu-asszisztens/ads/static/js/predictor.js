document.addEventListener('DOMContentLoaded', function() {
    
    const brandSelect = document.getElementById('brandSelect');
    const modelSelect = document.getElementById('modelSelect');
    const fuelSelect = document.getElementById('fuelSelect');
    
    const form = document.querySelector('form');
    const submitBtn = form.querySelector('button[type="submit"]');
    const inputs = form.querySelectorAll('input, select');

    // Rejtett adatok kinyerése a formból (amiket a Django küldött vissza)
    const savedModel = form ? form.getAttribute('data-model') : '';
    const savedFuel = form ? form.getAttribute('data-fuel') : '';

    // Egyedi validációs üzenetek beállítása minden input mezőre
    function updateCustomValidationMessages() {
        inputs.forEach(input => {
            if (input.validity.valueMissing) {
                if (input.tagName === 'SELECT') {
                    input.setCustomValidity('Kérjük, válasszon a listából!');
                } else {
                    input.setCustomValidity('Kérjük, töltse ki ezt a mezőt!');
                }
            } else if (input.validity.rangeUnderflow) {
                input.setCustomValidity('Az érték nem lehet kisebb, mint ' + input.min + '!');
            } else if (input.validity.rangeOverflow) {
                input.setCustomValidity('Az érték nem lehet nagyobb, mint ' + input.max + '!');
            } else {
                input.setCustomValidity(''); 
            }
        });
    }

    // Ellenőrizzük a form érvényességét és engedélyezzük vagy letiltjuk a submit gombot
    function checkFormValidity() {
        if (!submitBtn) return;
        updateCustomValidationMessages(); 

        let isValid = true;
        inputs.forEach(input => {
            if (input.disabled || input.value === "" || !input.checkValidity()) {
                isValid = false;
            }
        });
        
        submitBtn.disabled = !isValid;
    }

    if (submitBtn) submitBtn.disabled = true;
    updateCustomValidationMessages();

    inputs.forEach(input => {
        input.addEventListener('input', checkFormValidity);
        input.addEventListener('change', checkFormValidity);
        input.addEventListener('invalid', function() {
            updateCustomValidationMessages();
        });
    });

    if (form) form.addEventListener('change', checkFormValidity);

    // Dinamikus modellbetöltés a márka kiválasztása után
    function loadModels(brand, autoSelectModel = '') {
        modelSelect.disabled = true;
        modelSelect.innerHTML = '<option value="" disabled selected>Betöltés...</option>';
        fuelSelect.disabled = true;
        fuelSelect.innerHTML = '<option value="" disabled selected>Előbb válassz modellt!</option>';
        checkFormValidity();

        fetch(`/api/get-models/?brand=${encodeURIComponent(brand)}`)
            .then(response => response.json())
            .then(data => {
                modelSelect.innerHTML = '<option value="" disabled selected>Válassz modellt...</option>';
                data.forEach(function(modelName) {
                    var option = document.createElement('option');
                    option.value = modelName;
                    option.textContent = modelName;
                    modelSelect.appendChild(option);
                });
                modelSelect.disabled = false;
                
                // Ha van visszatöltendő modellünk, kiválasztjuk, majd indítjuk az üzemanyagok betöltését
                if (autoSelectModel && data.includes(autoSelectModel)) {
                    modelSelect.value = autoSelectModel;
                    loadFuels(brand, autoSelectModel, savedFuel);
                }
                checkFormValidity();
            })
            .catch(error => console.error("Hiba a modellek betöltésekor:", error));
    }

    // Dinamikus üzemanyag betöltés a modell kiválasztása után
    function loadFuels(brand, model, autoSelectFuel = '') {
        fuelSelect.disabled = true;
        fuelSelect.innerHTML = '<option value="" disabled selected>Betöltés...</option>';
        checkFormValidity();

        fetch(`/api/get-fuels/?brand=${encodeURIComponent(brand)}&model=${encodeURIComponent(model)}`)
            .then(response => response.json())
            .then(data => {
                fuelSelect.innerHTML = '<option value="" disabled selected>Válassz üzemanyagot...</option>';
                data.forEach(function(fuelName) {
                    var option = document.createElement('option');
                    option.value = fuelName;
                    option.textContent = fuelName;
                    fuelSelect.appendChild(option);
                });
                fuelSelect.disabled = false;
                
                // Ha van visszatöltendő üzemanyagunk, kiválasztjuk
                if (autoSelectFuel && data.includes(autoSelectFuel)) {
                    fuelSelect.value = autoSelectFuel;
                }
                checkFormValidity();
            })
            .catch(error => console.error("Hiba az üzemanyag betöltésekor:", error));
    }

    // Eseménykezelők a kézi váltásokhoz
    brandSelect.addEventListener('change', function() {
        loadModels(this.value);
    });

    modelSelect.addEventListener('change', function() {
        loadFuels(brandSelect.value, this.value);
    });

    // Ha a Django már kiválasztott egy márkát, azonnal lekérjük a hozzá tartozó modelleket
    if (brandSelect.value) {
        loadModels(brandSelect.value, savedModel);
    }
});
