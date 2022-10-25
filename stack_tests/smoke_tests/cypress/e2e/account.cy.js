/* global cy before Cypress */

describe('Account details page', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
  })

  it('can see page', () => {
    cy.contains('Settings').click()
    cy.title().should('eq', 'Account details')
  })
})
