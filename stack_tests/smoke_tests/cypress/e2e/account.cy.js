/* global cy before Cypress */

describe('Account details page', () => {
  beforeEach(() => {
    cy.session('login', cy.login, {cacheAcrossSpecs: true})
  })

  it('can see page', () => {
    cy.contains('Settings').click()
    cy.title().should('eq', 'Account details')
  })
})
