/* global cy before Cypress */

const organisationName = 'Doncaster College'

describe('Case overview', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/')
  })

  it('can edit case details', () => {
    cy.visit('/cases/')
    cy.get('[name="case_search"]').clear().type(`${organisationName}{enter}`)
    cy.contains(organisationName).click()
    cy.title().should('eq', `${organisationName} | Case overview`)

    cy.get('details').contains('Post case').click()
    cy.contains(/^Statement enforcement$/).click()
    cy.title().should('eq', `${organisationName} | Statement enforcement`)
  })
})
