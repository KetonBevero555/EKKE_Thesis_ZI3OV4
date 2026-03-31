document.addEventListener('DOMContentLoaded', function() {
    
    const brandSelect = document.getElementById('brandSelect');
    const modelSelect = document.getElementById('modelSelect');
    const fuelSelect = document.getElementById('fuelSelect');

    // Amikor a márka megváltozik -> frissítjük a modelleket
    brandSelect.addEventListener('change', function() {
        const brand = this.value;
        
        modelSelect.disabled = true;
        modelSelect.innerHTML = '<option value="" disabled selected>Betöltés...</option>';
        
        fuelSelect.disabled = true;
        fuelSelect.innerHTML = '<option value="" disabled selected>Előbb válassz modellt!</option>';

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
            })
            .catch(error => console.error("Hiba a modellek betöltésekor:", error));
    });

    // Amikor a modell megváltozik -> frissítjük az Üzemanyagokat
    modelSelect.addEventListener('change', function() {
        const brand = brandSelect.value;
        const model = this.value;

        fuelSelect.disabled = true;
        fuelSelect.innerHTML = '<option value="" disabled selected>Betöltés...</option>';

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
            })
            .catch(error => console.error("Hiba az üzemanyag betöltésekor:", error));
    });
});