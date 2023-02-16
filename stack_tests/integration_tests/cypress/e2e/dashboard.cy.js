/* global cy before Cypress */

describe('Dashboard page', () => {
  beforeEach(() => {
    cy.session('login', cy.login, {cacheAcrossSpecs: true})
    cy.visit('/')
  })

  it('can see page', () => {
    cy.title().should('eq', 'Home | Your cases')
  })

  it('can open accordion', () => {
    cy.get('button.govuk-accordion__show-all')
      .should('have.attr', 'aria-expanded')
      .then((ariaExpanded) => {
        if (ariaExpanded === 'true') {
          cy.contains('button', 'Hide all sections').click()
          cy.get('button.govuk-accordion__show-all').should('have.attr', 'aria-expanded', 'false')
        } else {
          cy.contains('button', 'Show all sections').click()
          cy.get('button.govuk-accordion__show-all').should('have.attr', 'aria-expanded', 'true')
        }
      })
  })
})
