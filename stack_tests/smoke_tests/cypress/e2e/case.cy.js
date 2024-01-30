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

    cy.get('[id="edit-case-details"]').click()
    cy.title().should('eq', `${organisationName} | Case details`)
    cy.contains('Case').click()

    cy.get('[id="edit-test-results"]').click()
    cy.title().should('eq', `${organisationName} | Testing details`)
    cy.contains('Case').click()

    cy.get('[id="edit-qa-ready-for-process"]').click()
    cy.title().should('eq', `${organisationName} | Report ready for QA process`)
    cy.contains('Case').click()

    cy.get('[id="edit-qa-auditor"]').click()
    cy.title().should('eq', `${organisationName} | QA auditor`)
    cy.contains('Case').click()

    cy.get('[id="edit-qa-comments"]').click()
    cy.title().should('eq', `${organisationName} | QA comments`)
    cy.contains('Case').click()

    cy.get('[id="edit-qa-report-approved"]').click()
    cy.title().should('eq', `${organisationName} | Report approved`)
    cy.contains('Case').click()

    cy.get('[id="edit-report-details"]').click()
    cy.title().should('eq', `${organisationName} | Report details`)
    cy.contains('Case').click()

    cy.get('[id="edit-contact-details"]').click()
    cy.title().should('eq', `${organisationName} | Contact details`)
    cy.contains('Case').click()

    cy.get('[id="edit-review-changes"]').click()
    cy.title().should('eq', `${organisationName} | Reviewing changes`)
    cy.contains('Case').click()

    cy.get('[id="edit-case-close"]').click()
    cy.title().should('eq', `${organisationName} | Closing the case`)
  })
})
