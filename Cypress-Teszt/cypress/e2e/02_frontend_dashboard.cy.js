describe('02 - Vezérlőpult UI és Navigáció', () => {
  beforeEach(() => {
    // 1. Bejelentkezés a Dashboard-ra
    cy.visit('http://127.0.0.1:8000/dashboard/');
    cy.get('input[name="username"]').type(Cypress.env('username'));
    cy.get('input[name="password"]').type(Cypress.env('admin_password'));
    cy.get('.submit-row > input').click();
  });

  it('Dashboard elemeinek átfogó ellenőrzése', () => {
    // Cím ellenőrzése
    cy.url().should('include', '/dashboard/');
    cy.get('h2').should('be.visible').and('contain', 'Rendszer Statisztikák');

    // Navigációs gombok ellenőrzése felül
    cy.get('.btn').contains('Árbecslő MI').should('be.visible').and('have.class', 'btn-outline-light');
    cy.get('.btn').contains('Vezérlőpult').should('be.visible').and('have.class', 'btn-primary');

    // A 4 statisztika kártya létezésének és tartalmának ellenőrzése
    cy.contains('Historikus Adatbázis').should('be.visible');
    cy.contains('autó').should('be.visible');

    cy.contains('Feldolgozás Alatt').should('be.visible');
    cy.contains('hirdetés').should('be.visible');

    cy.contains('MI Pontosság (R2)').should('be.visible');
    cy.contains('%').should('be.visible');

    cy.contains('Átlagos Tévedés (MAE)').should('be.visible');
    cy.contains('Ft').should('be.visible');

    // A CatBoost súlyozás szekció ellenőrzése
    cy.contains('CatBoost Döntési Súlyozás').should('be.visible');
    
    // Ellenőrizzük, hogy mind a 6 paraméter megjelenik-e
    cy.get('.progress-bar').should('have.length', 6);
    cy.contains('Évjárat').should('be.visible');
    cy.contains('Teljesítmény').should('be.visible');
    cy.contains('Futásteljesítmény').should('be.visible');
    cy.contains('Márka').should('be.visible');
    cy.contains('Modell').should('be.visible');
    cy.contains('Üzemanyag').should('be.visible');

    // ScrapeLog táblázat ellenőrzése
    cy.contains('Utolsó 20 Adatgyűjtés').should('be.visible');
    cy.get('table').should('be.visible');
    cy.get('th').contains('Kezdés').should('be.visible');
    cy.get('th').contains('Státusz').should('be.visible');

    // Visszanavigálás a főoldalra
    cy.get('.btn').contains('Árbecslő MI').click();
    
    // Főoldali ellenőrzés bejelentkezett állapotban
    cy.url().should('eq', 'http://127.0.0.1:8000/');
    cy.get('h2').should('contain', 'Használtautó Árbecslő MI');
    
    // Mivel be vagyunk jelentkezve, a Vezérlőpult gombnak látszania kell a főoldalon is
    cy.get('.btn').contains('Vezérlőpult').should('be.visible');
  });
});
