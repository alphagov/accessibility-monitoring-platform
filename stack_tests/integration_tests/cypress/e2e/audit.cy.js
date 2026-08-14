/* global cy before Cypress */

const accessibilityStatementURL = 'https://example.com/accessibility-statement'
const errorText = 'Error detail text'
const statementCheckResultComment = "Statement check result comment"
const reportOptionsNote = 'Report options note'

describe('View test', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/simplified/1/view')
  })

  it('can edit test metadata', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Initial test metadata$/).click()
    cy.contains('Populate with today\'s date').click()
    cy.get('#id_screen_size').select('15 inch')
    cy.get('[name="exemptions_state"]').check('no')
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
  })

  it('can edit pages', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Add or remove pages$/).click()
    cy.get('[name="standard-4-url"]').clear().type(accessibilityStatementURL)
    cy.get('[name="pages_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit a page', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Home page test$/).click()
    cy.get('[name="form-0-check_result_state"]').check('error')
    cy.get('[name="form-0-notes"]').clear().type(errorText)
    cy.get('[name="complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.contains(errorText)
  })

  it('can edit website compliance decision', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Compliance decision$/).click()
    cy.get('[name="compliance_state"]').check('partially-compliant')
    cy.get('[name="compliance_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
  })

  it('can edit WCAG test summary', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^WCAG summary$/).click()
    cy.get('[name="summary_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit accessibility statement check results', () => {
    cy.contains('Initial statement').click()
    cy.contains(/^Statement overview$/).click()
    cy.get('[name="form-0-check_result_state"]').check('yes')
    cy.get('[name="form-0-public_comment"]').clear().type(statementCheckResultComment)
    cy.get('[name="form-1-check_result_state"]').check('yes')
    cy.get('[name="statement_overview_complete_date"]').click()
    cy.contains('Save and continue').click()
    cy.get('[name="form-0-check_result_state"]').check('yes')
    cy.get('[name="statement_website_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.contains(statementCheckResultComment)
  })

  it('can edit accessibility statement compliance decision', () => {
    cy.contains('Initial statement').click()
    cy.contains(/^Statement compliance$/).click()
    cy.get('[name="compliance_state"]').check('not-compliant')
    cy.get('[name="compliance_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
  })
})
