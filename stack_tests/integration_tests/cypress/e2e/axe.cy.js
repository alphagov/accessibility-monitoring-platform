/* global cy before Cypress */

describe('Axe core checks', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
  })

  it('home page', () => {
    cy.injectAxe()
    cy.checkA11y(null, {
      includedImpacts: ['critical', 'serious']
    })
  })

  it('search page', () => {
    cy.visit('/cases/')
    cy.injectAxe()
    cy.checkA11y(null, {
      includedImpacts: ['critical', 'serious']
    })
  })
})
