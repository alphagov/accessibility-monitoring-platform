/* global cy before Cypress */

const exemptionsNote = 'Test exemptions note'
const accessibilityStatementURL = 'https://example.com/accessibility-statement'
const errorText = 'Error detail text'
const statementCheckResultComment = "Statement check result comment"
const websiteComplianceNote = 'Website compliance note'
const accessibilityStatementComplianceNote = 'Accessibility statement compliance note'
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
    cy.get('[name="exemptions_notes"]').clear().type(exemptionsNote)
    cy.get('[name="audit_metadata_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Simplified case$/).click()
    cy.contains(exemptionsNote)
  })

  it('can edit pages', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Add or remove pages$/).click()
    cy.get('[name="standard-4-url"]').clear().type(accessibilityStatementURL)
    cy.get('[name="audit_pages_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit a page', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Home page test$/).click()
    cy.get('[name="form-0-check_result_state"]').check('error')
    cy.get('[name="form-0-notes"]').clear().type(errorText)
    cy.get('[name="complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Simplified case$/).click()
    cy.contains(errorText)
  })

  it('can edit website compliance decision', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Compliance decision$/).click()
    cy.get('[name="case-compliance-website_compliance_state_initial"]').check('partially-compliant')
    cy.get('[name="case-compliance-website_compliance_notes_initial"]').clear().type(websiteComplianceNote)
    cy.get('[name="audit_website_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Simplified case$/).click()
    cy.contains(websiteComplianceNote)
  })

  it('can edit WCAG test summary', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^WCAG summary$/).click()
    cy.get('[name="audit_wcag_summary_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit accessibility statement check results', () => {
    cy.contains('Initial statement').click()
    cy.contains(/^Statement overview$/).click()
    cy.get('[name="form-0-check_result_state"]').check('yes')
    cy.get('[name="form-0-report_comment"]').clear().type(statementCheckResultComment)
    cy.get('[name="form-1-check_result_state"]').check('yes')
    cy.get('[name="audit_statement_overview_complete_date"]').click()
    cy.contains('Save and continue').click()
    cy.get('[name="form-0-check_result_state"]').check('yes')
    cy.get('[name="audit_statement_website_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Simplified case$/).click()
    cy.contains(statementCheckResultComment)
  })

  it('can edit accessibility statement compliance decision', () => {
    cy.contains('Initial statement').click()
    cy.contains(/^Statement compliance$/).click()
    cy.get('[name="case-compliance-statement_compliance_state_initial"]').check('not-compliant')
    cy.get('[name="case-compliance-statement_compliance_notes_initial"]').clear().type(accessibilityStatementComplianceNote)
    cy.get('[name="audit_statement_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Simplified case$/).click()
    cy.contains(accessibilityStatementComplianceNote)
  })
})
