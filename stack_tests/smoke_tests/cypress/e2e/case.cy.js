/* global cy before Cypress */

const organisationName = 'Doncaster College'

describe('View case', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/')
  })

  it('can edit case details', () => {
    cy.visit('/cases/')
    cy.get('[name="case_search"]').clear().type(`${organisationName}{enter}`)
    cy.contains(organisationName).click()
    cy.title().should('eq', `${organisationName} | View case`)

    cy.contains('Post case (0/0)').click()
    cy.get('[id="edit-cases996statement-enforcement"]').click()
    cy.title().should('eq', `${organisationName} | Statement enforcement`)
  })
})
