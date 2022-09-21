/* global cy before Cypress */

const organisationName = 'ExampleCorp'
const caseDetailsNotes = 'Case details note'

describe('View case', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
    cy.visit('/cases/1/view')
  })

  it('can edit case details', () => {
    cy.contains('Edit case details').click()
    cy.get('[name="notes"]').type(caseDetailsNotes)
    cy.get('[name="case_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.title().should('eq', `${organisationName} | View case`)
    cy.contains(caseDetailsNotes)
  })

  it('can edit testing details', () => {
    cy.contains('Edit testing details').click()
    cy.get('[name="testing_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.title().should('eq', `${organisationName} | View case`)
  })
})
