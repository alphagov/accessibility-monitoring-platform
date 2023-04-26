/* global cy before Cypress */

const organisationName = 'Doncaster College'

describe('View case', () => {
  beforeEach(() => {
    cy.session('login', cy.login, {cacheAcrossSpecs: true})
    cy.visit('/')
  })

  it('can edit case details', () => {
    cy.visit('/cases/')
    cy.get('[name="case_search"]').clear().type(`${organisationName}{enter}`)
    cy.contains(organisationName).click()
    cy.title().should('eq', `${organisationName} | View case`)
    
    cy.get('[id="edit-case-details"]').click()
    cy.title().should('eq', `${organisationName} | Case details`)
    cy.contains('Case').click()

    cy.get('[id="edit-test-results"]').click()
    cy.title().should('eq', `${organisationName} | Testing details`)
    cy.contains('Case').click()

    cy.get('[id="edit-qa-process"]').click()
    cy.title().should('eq', `${organisationName} | QA process`)
    cy.contains('Case').click()

    cy.get('[id="edit-report-details"]').click()
    cy.title().should('eq', `${organisationName} | Report details`)
    cy.contains('Case').click()

    cy.get('[id="edit-contact-details"]').click()
    cy.title().should('eq', `${organisationName} | Contact details`)
    cy.contains('Case').click()

    cy.get('[id="edit-report-correspondence"]').click()
    cy.title().should('eq', `${organisationName} | Report correspondence`)
    cy.contains('Case').click()

    cy.get('[id="edit-review-changes"]').click()
    cy.title().should('eq', `${organisationName} | Reviewing changes`)
    cy.contains('Case').click()

    cy.get('[id="edit-case-close"]').click()
    cy.title().should('eq', `${organisationName} | Closing the case`)
    cy.contains('Case').click()

    cy.get('[id="edit-enforcement-body-correspondence"]').click()
    cy.title().should('eq', `${organisationName} | Equality body summary`)
    cy.contains('Case').click()

    cy.get('[id="edit-post-case"]').click()
    cy.title().should('eq', `${organisationName} | Post case summary`)
  })
})
