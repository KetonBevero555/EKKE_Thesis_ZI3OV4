describe('03 - Adatmegőrzés és Határérték (Boundary) Tesztelés', () => {
  beforeEach(() => {
    cy.visit('http://127.0.0.1:8000/');
  });

  it('Helyes adatokkal becslés, majd az űrlap adatmegőrzésének ellenőrzése', () => {
    // Kitölti az űrlapot helyes adatokkal
    cy.get('#brandSelect').select('OPEL');
    cy.wait(1000);
    cy.get('#modelSelect').select('ASTRA');
    cy.wait(500);
    cy.get('#fuelSelect').select('Benzin');

    cy.get('input[name="year"]').type('2015');
    cy.get('input[name="mileage"]').type('150000');
    cy.get('input[name="engine_cc"]').type('1598');
    cy.get('input[name="power_le"]').type('115');

    // Becslés indítása
    cy.get('button[type="submit"]').click();

    // Eredmény ellenőrzése
    cy.get('.alert-success').should('be.visible').and('contain', 'Ft');

    // Ellenőrizzük, hogy a beírt adatok visszatöltődtek-e a mezőkbe
    cy.get('#brandSelect').should('have.value', 'OPEL');
    cy.get('#modelSelect').should('have.value', 'ASTRA');
    cy.get('#fuelSelect').should('have.value', 'Benzin');
    cy.get('input[name="year"]').should('have.value', '2015');
    cy.get('input[name="mileage"]').should('have.value', '150000');
    cy.get('input[name="engine_cc"]').should('have.value', '1598');
    cy.get('input[name="power_le"]').should('have.value', '115');
  });

  it('Határon túli (invalid) értékek tesztelése a beviteli mezőkön', () => {
    // Kitölti az űrlapot helyes adatokkal
    cy.get('#brandSelect').select('OPEL');
    cy.wait(1000);
    cy.get('#modelSelect').select('ASTRA');
    cy.wait(500);
    cy.get('#fuelSelect').select('Benzin');

    // Évjárat teszt (min: 1880, max: aktuális év)
    const nextYear = new Date().getFullYear() + 1;
    
    // Túl régi autót próbálunk beírni
    cy.get('input[name="year"]').type('1879');
    cy.get('input[name="year"]').should('match', ':invalid');
    
    // Jövőbeli autót próbálunk beírni
    cy.get('input[name="year"]').clear().type(`${nextYear}`);
    cy.get('input[name="year"]').should('match', ':invalid');

    // Helyes határértékre javítjuk
    cy.get('input[name="year"]').clear().type('1880');
    cy.get('input[name="year"]').should('match', ':valid');

    // Futásteljesítmény teszt (min: 0)
    cy.get('input[name="mileage"]').type('-10');
    cy.get('input[name="mileage"]').should('match', ':invalid');
    cy.get('input[name="mileage"]').clear().type('0');
    cy.get('input[name="mileage"]').should('match', ':valid');

    // Hengerűrtartalom teszt (min: 500)
    cy.get('input[name="engine_cc"]').type('499');
    cy.get('input[name="engine_cc"]').should('match', ':invalid');
    cy.get('input[name="engine_cc"]').clear().type('500');
    cy.get('input[name="engine_cc"]').should('match', ':valid');

    // Lóerő teszt (min: 10)
    cy.get('input[name="power_le"]').type('9');
    cy.get('input[name="power_le"]').should('match', ':invalid');
    cy.get('input[name="power_le"]').clear().type('10');
    cy.get('input[name="power_le"]').should('match', ':valid');
    
    // Gomb aktivitásának ellenőrzése
    cy.get('input[name="power_le"]').clear().type('9');
    cy.get('input[name="power_le"]').should('match', ':invalid');
    
    // Mivel az adat hibás, ellenőrizzük, hogy a gomb nyomhatatlan-e
    cy.get('button[type="submit"]').should('be.disabled');

    // Kijavítjuk a hibás értéket egy helyesre
    cy.get('input[name="power_le"]').clear().type('10');
    cy.get('input[name="power_le"]').should('match', ':valid');
    
    // Mivel minden adat jó, a gombnak újra aktívnak (kattinthatónak) kell lennie
    cy.get('button[type="submit"]').should('not.be.disabled');
  });
});
