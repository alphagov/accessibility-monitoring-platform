/* global cy before Cypress */

const exemptionsNote = 'Test exemptions note'
const accessibilityStatementURL = 'https://example.com/accessibility-statement'
const errorText = 'Error detail text'
const websiteComplianceNote = 'Website compliance note'
const accessibilityStatementBackupURL = 'https://accessibility-statement-backup.com'
const accessibilityStatementComplianceNote = 'Accessibility statement compliance note'
const reportOptionsNote = 'Report options note'

describe('View test', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
    cy.visit('/audits/1/detail')
  })

  it('can edit test metadata', () => {
    cy.contains('a', 'Edit test metadata').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('#id_screen_size').select('15 inch')
    cy.get('[name="exemptions_state"]').check('no')
    cy.get('[name="exemptions_notes"]').clear().type(exemptionsNote)
    cy.get('[name="audit_metadata_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Test').click()
    cy.title().should('eq', 'ExampleCorp | View test')
    cy.contains(exemptionsNote)
  })

  it('can edit pages', () => {
    cy.contains('a', 'Edit pages').click()
    cy.get('[name="standard-2-url"]').clear().type(accessibilityStatementURL)
    cy.get('[name="audit_pages_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit a page', () => {
    cy.contains('a', 'Edit pages').click()
    cy.get('[data-cy="nav-step"]').contains('Home').click()
    cy.get('[name="form-0-check_result_state"]').check('error')
    cy.get('[name="form-0-notes"]').clear().type(errorText)
    cy.get('[name="complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Test').click()
    cy.contains(errorText)
  })

  it('can edit website compliance decision', () => {
    cy.contains('a', 'Edit website compliance decision').click()
    cy.get('[name="case-is_website_compliant"]').check('partially-compliant')
    cy.get('[name="case-compliance_decision_notes"]').clear().type(websiteComplianceNote)
    cy.get('[name="audit_website_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Test').click()
    cy.contains(websiteComplianceNote)
  })

  it('can edit accessibility statement', () => {
    cy.contains('a', 'Edit accessibility statement').click()
    cy.get('[name="accessibility_statement_backup_url"]').clear().type(accessibilityStatementBackupURL)
    cy.get('[name="scope_state"]').check('incomplete')
    cy.get('[name="audit_statement_1_complete_date"]').click()
    cy.contains('Save and continue').click()
    cy.get('[name="disproportionate_burden_state"]').check('assessment')
    cy.get('[name="audit_statement_2_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Test').click()
    cy.contains(accessibilityStatementBackupURL)
  })

  it('can edit accessibility statement compliance decision', () => {
    cy.contains('a', 'Edit accessibility statement compliance decision').click()
    cy.get('[name="case-accessibility_statement_state"]').check('not-compliant')
    cy.get('[name="case-accessibility_statement_notes"]').clear().type(accessibilityStatementComplianceNote)
    cy.get('[name="audit_statement_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Test').click()
    cy.contains(accessibilityStatementComplianceNote)
  })

  it('can edit report options', () => {
    cy.contains('a', 'Edit report options').click()
    cy.get('[name="accessibility_statement_state"]').check('found-but')
    cy.get('[name="accessibility_statement_not_correct_format"]').click()
    cy.get('[name="report_next_change_statement"]').click()
    cy.get('[name="report_options_notes"]').clear().type(reportOptionsNote)
    cy.get('[name="audit_report_options_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Test').click()
    cy.contains(reportOptionsNote)
  })

  it('can edit test summary', () => {
    cy.contains('a', 'Edit report options').click()
    cy.get('[data-cy="nav-step"]').contains('Test summary').click()
    cy.get('[name="audit_summary_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit report text', () => {
    cy.contains('a', 'Edit report text').click()
    cy.get('[name="audit_report_text_complete_date"]').click()
    cy.contains('Save').click()
  })
})
