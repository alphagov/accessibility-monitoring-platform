/* global cy before Cypress */

const retestMetadataNote = '12-week retest metadata note'
const retestErrorText = 'Retest error note'
const websiteComplianceNote = 'Website compliance note'
const statementCheckResultRetestComment = 'Statement check result retest comment'
const statementComplianceNote = 'Accessibility statement compliance note'

describe('12-week retest', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/cases/1/view')
  })

  it('can edit 12-week retest metadata', () => {
    cy.contains('12-week WCAG test').click()
    cy.get('#edit-audits1edit-audit-retest-metadata').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="audit_retest_metadata_notes"]').clear().type(retestMetadataNote)
    cy.get('[name="audit_retest_metadata_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', 'ExampleCorp | View case')
    cy.contains(retestMetadataNote)
  })

  it('can edit 12-week retesting home', () => {
    cy.contains('12-week WCAG test').click()
    cy.get('#edit-auditspages1edit-audit-retest-page-checks').click()
    cy.title().should('eq', 'ExampleCorp | Home page retest')
    cy.get('[name="form-0-retest_state"]').check('fixed')
    cy.get('[name="form-0-retest_notes"]').clear().type(retestErrorText)
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', 'ExampleCorp | View case')
    cy.contains(retestErrorText)
  })

  it('can edit 12-week website compliance decision', () => {
    cy.contains('12-week WCAG test').click()
    cy.get('#edit-audits1edit-retest-website-decision').click()
    cy.get('[name="case-compliance-website_compliance_state_12_week"]').check('compliant')
    cy.get('[name="case-compliance-website_compliance_notes_12_week"]').clear().type(websiteComplianceNote)
    cy.get('[name="audit_retest_website_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', 'ExampleCorp | View case')
    cy.contains(websiteComplianceNote)
  })

  it('can edit 12-week accessibility statement overview', () => {
    cy.contains('12-week statement').click()
    cy.get('#edit-audits1edit-retest-statement-overview').click()
    cy.get('[name="form-0-retest_state"]').check('yes')
    cy.get('[name="form-0-retest_comment"]').clear().type(statementCheckResultRetestComment)
    cy.get('[name="form-1-retest_state"]').check('yes')
    cy.get('[name="audit_retest_statement_overview_complete_date"]').click()
    cy.contains('Save and continue').click()
    cy.get('[name="audit_retest_statement_website_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', 'ExampleCorp | View case')
    cy.contains(statementCheckResultRetestComment)
  })

  it('can edit 12-week accessibility statement compliance decision', () => {
    cy.contains('12-week statement').click()
    cy.get('#edit-audits1edit-audit-retest-statement-decision').click()
    cy.get('[name="case-compliance-statement_compliance_state_12_week"]').check('compliant')
    cy.get('[name="case-compliance-statement_compliance_notes_12_week"]').clear().type(statementComplianceNote)
    cy.get('[name="audit_retest_statement_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', 'ExampleCorp | View case')
    cy.contains(statementComplianceNote)
  })
})
