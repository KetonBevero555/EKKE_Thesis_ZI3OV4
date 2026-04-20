describe('Hahu-asszisztens Teljes E2E és Navigációs Tesztelés', () => {

  beforeEach(() => {
    // Minden teszt előtt a főoldalra megyünk, be nem jelentkezett állapotban
    cy.visit('http://127.0.0.1:8000/');
  });

  it('1. UI elemek ellenőrzése és jogosultságkezelés (gomb hiánya)', () => {
    cy.get('h2').should('contain', 'Használtautó Árbecslő MI');
    
    // Ellenőrizzük, hogy vendégként NEM látszik a Vezérlőpult gomb
    cy.get('.btn-outline-light').should('not.exist');
    
    // Ellenőrizzük az MI statisztikai kártyát
    cy.get('.card').contains('Gép Aktuális Állapota').should('be.visible');
    cy.get('b.text-dark').first().should('not.contain', 'N/A');
  });

  it('2. Sikeres árbecslési folyamat (Első kör)', () => {
    cy.get('#brandSelect').select('Mazda');
    cy.wait(1000);
    cy.get('#modelSelect').select('Cx-5');
    cy.wait(500);
    cy.get('#fuelSelect').select('Dízel');

    cy.get('input[name="year"]').type('2015');
    cy.get('input[name="mileage"]').type('250000');
    cy.get('input[name="engine_cc"]').type('2200');
    cy.get('input[name="power_le"]').type('150');

    cy.get('button[type="submit"]').click();
    cy.get('.alert-success', { timeout: 10000 }).should('be.visible');
  });

  it('3. Bejelentkezés, Dashboard és visszatérés új becslésre', () => {
    // A: Bejelentkezés a Dashboard-ra (itt kényszerítjük az átirányítást)
    cy.visit('http://127.0.0.1:8000/dashboard/');
    
    // Bejelentkezés
    cy.get('input[name="username"]').type('ZI3OV4');
    cy.get('input[name="password"]').type('secretpassword123');
    cy.get('.submit-row > input').click();

    // B: Ellenőrizzük, hogy bejelentkezve már látszanak a statisztikák
    cy.url().should('include', '/dashboard/');
    cy.get('h2').should('contain', 'Rendszer Statisztikák');

    // C: Visszanavigálás - Itt a gombnak már léteznie kell, mert be vagyunk jelentkezve!
    // A HTML-ed alapján a Dashboardon a visszavezető gomb az 'Árbecslő MI'
    cy.get('.btn-outline-light').contains('Árbecslő MI').click();

    // D: Újabb becslés lefuttatása (Ford Focus)
    cy.url().should('eq', 'http://127.0.0.1:8000/');
    
    // Most, hogy be vagyunk jelentkezve, a főoldalon is meg kell jelennie a Vezérlőpult gombnak!
    cy.get('.btn-outline-light').should('be.visible').and('contain', 'Vezérlőpult');

    cy.get('#brandSelect').select('Ford');
    cy.wait(1000);
    cy.get('#modelSelect').select('Focus');
    cy.wait(500);
    cy.get('#fuelSelect').select('Benzin');

    cy.get('input[name="year"]').type('2018');
    cy.get('input[name="mileage"]').type('120000');
    cy.get('input[name="engine_cc"]').type('1596');
    cy.get('input[name="power_le"]').type('125');

    cy.get('button[type="submit"]').click();

    // E: Végső ellenőrzés
    cy.get('.alert-success', { timeout: 10000 }).should('be.visible');
  });
});