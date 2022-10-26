/* global cy before Cypress */

const organisationName = 'Met Office'

describe('View case', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
  })

  it('can edit case details', () => {
    cy.get('[name="search"]').clear().type(`${organisationName}{enter}`)
    cy.contains(organisationName).click()
    cy.title().should('eq', `${organisationName} | View case`)

    cy.contains('Edit case details').click()
    cy.title().should('eq', `${organisationName} | Case details`)
    cy.contains('Case').click()

    cy.contains('Edit testing details').click()
    cy.title().should('eq', `${organisationName} | Testing details`)
    cy.contains('Case').click()

    cy.contains('Edit report details').click()
    cy.title().should('eq', `${organisationName} | Report details`)
    cy.contains('Case').click()

    cy.contains('Edit contact details').click()
    cy.title().should('eq', `${organisationName} | Contact details`)
    cy.contains('Case').click()

    cy.contains('Edit report correspondence').click()
    cy.title().should('eq', `${organisationName} | Report correspondence`)
    cy.contains('Case').click()

    cy.contains('Edit reviewing changes').click()
    cy.title().should('eq', `${organisationName} | Reviewing changes`)
    cy.contains('Case').click()

    cy.contains('Edit final accessibility statement compliance decision').click()
    cy.title().should('eq', `${organisationName} | Final accessibility statement compliance decision`)
    cy.contains('Case').click()

    cy.contains('Edit closing the case').click()
    cy.title().should('eq', `${organisationName} | Closing the case`)
    cy.contains('Case').click()

    cy.contains('Edit post case summary').click()
    cy.title().should('eq', `${organisationName} | Post case summary`)
    cy.contains('Case').click()

    cy.contains('Edit equality body summary').click()
    cy.title().should('eq', `${organisationName} | Equality body summary`)
  })
})
