describe('04 - CatBoost Modell tömeges tesztelése (10 autó)', () => {
  const testCars = [
    { brand: 'SUZUKI', model: 'SWIFT', fuel: 'Benzin', year: '2008', mileage: '180000', engine_cc: '1328', power: '92' },
    { brand: 'OPEL', model: 'ASTRA', fuel: 'Benzin', year: '2012', mileage: '150000', engine_cc: '1598', power: '115' },
    { brand: 'VOLKSWAGEN', model: 'GOLF', fuel: 'Dízel', year: '2015', mileage: '220000', engine_cc: '1968', power: '150' },
    { brand: 'SKODA', model: 'OCTAVIA', fuel: 'Dízel', year: '2018', mileage: '140000', engine_cc: '1968', power: '150' },
    { brand: 'FORD', model: 'FOCUS', fuel: 'Benzin', year: '2016', mileage: '110000', engine_cc: '1596', power: '125' },
    { brand: 'TOYOTA', model: 'YARIS', fuel: 'Hibrid', year: '2020', mileage: '45000', engine_cc: '1497', power: '100' },
    { brand: 'BMW', model: '320', fuel: 'Dízel', year: '2011', mileage: '280000', engine_cc: '1995', power: '184' },
    { brand: 'AUDI', model: 'A4', fuel: 'Dízel', year: '2014', mileage: '200000', engine_cc: '1968', power: '190' },
    { brand: 'HONDA', model: 'CIVIC', fuel: 'Benzin', year: '2009', mileage: '160000', engine_cc: '1799', power: '140' },
    { brand: 'KIA', model: 'CEED', fuel: 'Benzin', year: '2019', mileage: '60000', engine_cc: '1396', power: '140' }
  ];

  beforeEach(() => {
    cy.visit('http://127.0.0.1:8000/');
    cy.get('select[name="ai_type"]').select('catboost');
  });

  testCars.forEach((car, index) => {
    it(`Teszt #${index + 1}: ${car.brand} ${car.model} (${car.year}) becslése CB modellel`, () => {
      // Kitöltjük az űrlapot a tesztadatokkal
      cy.get('#brandSelect').select(car.brand);
      cy.wait(500);
      cy.get('#modelSelect').should('not.be.disabled').select(car.model);
      cy.wait(200);
      cy.get('#fuelSelect').should('not.be.disabled').select(car.fuel);

      cy.get('input[name="year"]').clear().type(car.year);
      cy.get('input[name="mileage"]').clear().type(car.mileage);
      cy.get('input[name="engine_cc"]').clear().type(car.engine_cc);
      cy.get('input[name="power_le"]').clear().type(car.power);

      cy.get('button[type="submit"]').click();
      
      // Az eredménynek forintban kell megjelennie
      cy.get('.alert-success', { timeout: 10000 }).should('be.visible').and('contain', 'Ft');
      cy.get('select[name="ai_type"]').should('have.value', 'catboost');
    });
  });
});
