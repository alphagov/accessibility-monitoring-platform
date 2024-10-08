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

    cy.get('[id="edit-case-metadata"]').click()
    cy.title().should('eq', `${organisationName} | Case metadata`)
    cy.contains(/^Case$/).click()

    cy.get('[id="edit-audit-metadata"]').click()
    cy.title().should('eq', `${organisationName} | Initial test metadata`)
    cy.contains(/^Case$/).click()

    cy.get('[id="edit-qa-comments"]').click()
    cy.title().should('eq', `${organisationName} | Comments (2)`)
    cy.contains(/^Case$/).click()

    cy.get('[id="edit-qa-approval"]').click()
    cy.title().should('eq', `${organisationName} | QA approval`)
    cy.contains(/^Case$/).click()

    cy.get('[id="edit-publish-report"]').click()
    cy.title().should('eq', `${organisationName} | Publish report`)
    cy.contains(/^Case$/).click()

    cy.get('[id="manage-contact-details"]').click()
    cy.title().should('eq', `${organisationName} | Manage contact details`)
    cy.contains(/^Case$/).click()

    cy.get('[id="edit-review-changes"]').click()
    cy.title().should('eq', `${organisationName} | Reviewing changes`)
    cy.contains(/^Case$/).click()

    cy.get('[id="edit-enforcement-recommendation"]').click()
    cy.title().should('eq', `${organisationName} | Recommendation`)
    cy.contains(/^Case$/).click()

    cy.get('[id="edit-case-close"]').click()
    cy.title().should('eq', `${organisationName} | Closing the case`)
  })
})
