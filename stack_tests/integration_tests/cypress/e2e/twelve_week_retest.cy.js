/* global cy before Cypress */

const retestErrorText = 'Retest error note'
const statementCheckResultRetestComment = 'Statement check result retest comment'

describe('12-week retest', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/simplified/1/view')
  })

  it('can edit 12-week retest metadata', () => {
    cy.contains('12-week WCAG test').click()
    cy.contains(/^12-week retest metadata$/).click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="audit_retest_metadata_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.title().should('eq', 'example.com · Simplified Organisation | Simplified case overview')
  })

  it('can edit 12-week retesting home', () => {
    cy.contains('12-week WCAG test').click()
    cy.contains(/^Home page retest$/).click()
    cy.title().should('eq', 'example.com · Simplified Organisation | Home page retest')
    cy.get('[name="form-0-retest_state"]').check('fixed')
    cy.get('[name="form-0-retest_notes"]').clear().type(retestErrorText)
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.title().should('eq', 'example.com · Simplified Organisation | Simplified case overview')
    cy.contains(retestErrorText)
  })
})
