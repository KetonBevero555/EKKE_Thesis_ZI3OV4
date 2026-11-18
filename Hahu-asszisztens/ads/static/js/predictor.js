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

    // Ellenőrizzük a form érvényességét, és csak a gomb tiltásával/engedélyezésével foglalkozunk
    function checkFormValidity() {
        if (!submitBtn) return;

        let isValid = true;
        inputs.forEach(input => {
            if (input.disabled) {
                // Ha a mező le van tiltva, az alapból blokkolja a gombot (pl. mert még tölt a modell/üzemanyag lista)
                // KIVÉVE: Ha a hengerűrtartalomról van szó, mert azt 'Elektromos' üzemanyagnál szándékosan tiltjuk le!
                if (input.name !== 'engine_cc') {
                    isValid = false;
                }
            } else {
                // Ha a mező aktív, akkor ki kell lennie töltve, és meg kell felelnie a HTML szabályoknak (pl. min/max értékek)
                if (input.value === "" || !input.checkValidity()) {
                    isValid = false;
                }
            }
        });
        
        submitBtn.disabled = !isValid;
    }

    if (submitBtn) submitBtn.disabled = true;

    // Eseményfigyelők az inputokra
    inputs.forEach(input => {
        input.addEventListener('input', checkFormValidity);
        input.addEventListener('change', checkFormValidity);
    });

    if (form) form.addEventListener('change', checkFormValidity);

    // Hengerűrtartalom mező kezelése "Elektromos" üzemanyag esetén
    if (fuelSelect) {
        fuelSelect.addEventListener('change', function() {
            const engineInput = document.querySelector('input[name="engine_cc"]');
            if (this.value === 'Elektromos') {
                engineInput.disabled = true;
                engineInput.value = '';
                engineInput.placeholder = 'Elektromosnál nem szükséges';
            } else {
                engineInput.disabled = false;
                engineInput.placeholder = '1600';
            }
            checkFormValidity();
        });
    }

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
                
                // Ha van visszatöltendő modellünk
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
                
                // Ha van visszatöltendő üzemanyagunk
                if (autoSelectFuel && data.includes(autoSelectFuel)) {
                    fuelSelect.value = autoSelectFuel;
                    // Manuálisan indítunk egy 'change' eseményt, hogy ha visszatöltöttük az "Elektromost", akkor rögtön tiltsa le a ccm-t
                    fuelSelect.dispatchEvent(new Event('change'));
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

    // Ha a Django már kiválasztott egy márkát
    if (brandSelect.value) {
        loadModels(brandSelect.value, savedModel);
    }
});
