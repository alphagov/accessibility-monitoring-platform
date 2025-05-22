/* global cy before Cypress */

describe('Dashboard page', () => {
  beforeEach(() => {
    cy.session('login', cy.login, {cacheAcrossSpecs: true})
    cy.visit('/')
  })

  it('can see page', () => {
    cy.title().should('eq', 'Home | Your simplified cases')
  })
})
