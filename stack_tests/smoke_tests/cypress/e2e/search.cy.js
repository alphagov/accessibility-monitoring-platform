/* global cy before Cypress */

describe('Search page', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
    cy.visit('/cases/')
  })

  it('can see page', () => {
    cy.title().should('eq', 'Search')
  })

  it('can do search', () => {
    cy.contains('Anglesey Council').should('not.exist')
    cy.get('[name="search"]').clear().type('1{enter}')
    cy.contains('Anglesey Council')
  })
})
