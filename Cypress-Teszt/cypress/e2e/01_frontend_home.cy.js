describe('01 - Főoldal UI, Form interakciók és Jogosultságok', () => {
  beforeEach(() => {
    cy.visit('http://127.0.0.1:8000/');
  });

  it('Teljes UI vizsgálat, adatkitöltés és becslés futtatása vendégként', () => {
    
    // Weboldal cím kiírás ellenőrzése
    cy.get('h2').should('be.visible').and('contain', 'Használtautó Árbecslő MI');

    // Vezérlőpult gomb nem látszódik vendégként
    cy.contains('.btn', 'Vezérlőpult').should('not.exist');

    // CB modell és megjelenített statisztikái (Alapértelmezett)
    cy.get('select[name="ai_type"]').should('have.value', 'catboost');
    cy.get('#stats-catboost').should('be.visible').and('contain', 'CatBoost');
    cy.get('#stats-rf').should('not.be.visible');

    // RF modell és megjelenített statisztikái (Váltás után)
    cy.get('select[name="ai_type"]').select('random_forest');
    cy.get('#stats-rf').should('be.visible').and('contain', 'Random Forest');
    cy.get('#stats-catboost').should('not.be.visible');
    
    // Visszaváltunk CatBoostra a teszteléshez
    cy.get('select[name="ai_type"]').select('catboost');

    // Márka választó ellenőrzése és választás
    cy.get('#brandSelect').should('exist').and('be.visible');
    cy.get('#brandSelect').select('FORD');
    cy.wait(1000);

    // Modell választó ellenőrzése és választás
    cy.get('#modelSelect').should('exist').and('not.be.disabled');
    cy.get('#modelSelect').select('FOCUS');
    cy.wait(500);

    // Üzemanyag választó ellenőrzése és választás
    cy.get('#fuelSelect').should('exist').and('not.be.disabled');
    cy.get('#fuelSelect').select('Benzin');

    // Évjárat beírása
    cy.get('input[name="year"]').should('exist').clear().type('2018');

    // Futásteljesítmény beírása
    cy.get('input[name="mileage"]').should('exist').clear().type('120000');

    // Hengerűrtartalom beírása (A beküldött HTML-ben benne van a mező)
    cy.get('input[name="engine_cc"]').should('exist').clear().type('1596');

    // Lóerő beírása
    cy.get('input[name="power_le"]').should('exist').clear().type('125');

    // Becslés gomb létezik-e
    cy.get('button[type="submit"]').should('exist').and('be.visible').and('contain', 'Becslés Indítása');

    // Becslés
    cy.get('button[type="submit"]').click();

    // Ezután megjelenik-e az ár (Az oldal újratöltődik a POST kérés miatt)
    cy.get('.alert-success', { timeout: 10000 }).should('be.visible').and('contain', 'Ft');
    
    // Extra ellenőrzés a becslés után: Vezérlőpult gomb továbbra sem látszik
    cy.contains('.btn', 'Vezérlőpult').should('not.exist');
  });
});
