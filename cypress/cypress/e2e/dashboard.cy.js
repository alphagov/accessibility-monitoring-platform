/* global cy before Cypress */

describe('Dashboard page', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
    cy.visit('/')
  })

  it('can see page', () => {
    cy.title().should('eq', 'Dashboard | Your cases')
  })
})
