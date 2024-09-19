/* global cy before after Cypress */

describe('Report publisher', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/cases/1/edit-report-ready-for-qa')
  })

  it('contains link to latest published HTML report', () => {
    cy.contains('View report')
      .should('have.attr', 'href')
      .then((href) => {
        expect(href).to.include('/reports/96b1afce-a445-42c3-961c-7708aba196f3')
      })
  })
})
