/* global cy before Cypress */

const retestMetadataNote = '12-week retest metadata note'
const retestErrorText = 'Retest error note'
const websiteComplianceNote = 'Website compliance note'
const scopeNote = 'Accessibility statement scope note'
const disproportionateNote = 'Disproportionate burden note'
const statementComplianceNote = 'Accessibility statement compliance note'

describe('View test', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/audits/1/audit-retest-detail')
  })

  it('can edit 12-week test metadata', () => {
    cy.get('#edit-audit-retest-metadata').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="audit_retest_metadata_notes"]').clear().type(retestMetadataNote)
    cy.get('[name="audit_retest_metadata_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('12-week test').click()
    cy.title().should('eq', 'ExampleCorp | View 12-week test')
    cy.contains(retestMetadataNote)
  })

  it('can edit retesting home', () => {
    cy.get('a[data-cy="content-page-link"]').eq(0).click()
    cy.title().should('eq', 'ExampleCorp | Retesting Home')
    cy.get('[name="form-0-retest_state"]').check('fixed')
    cy.get('[name="form-0-retest_notes"]').clear().type(retestErrorText)
    cy.contains('Save').click()
    cy.contains('12-week test').click()
    cy.contains(retestErrorText)
  })

  it('can edit 12-week pages comparison', () => {
    cy.get('#edit-audit-retest-pages-comparison').click()
    cy.get('[name="audit_retest_pages_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week website compliance decision', () => {
    cy.get('#edit-audit-retest-website-decision').click()
    cy.get('[name="case-compliance-website_compliance_state_12_week"]').check('compliant')
    cy.get('[name="case-compliance-website_compliance_notes_12_week"]').clear().type(websiteComplianceNote)
    cy.get('[name="audit_retest_website_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('12-week test').click()
    cy.contains(websiteComplianceNote)
  })

  it('can edit 12-week accessibility statement', () => {
    cy.get('#edit-audit-retest-statement-1').click()
    cy.get('[name="archive_audit_retest_scope_state"]').check('present')
    cy.get('[name="archive_audit_retest_scope_notes"]').clear().type(scopeNote)
    cy.get('[name="archive_audit_retest_statement_1_complete_date"]').click()
    cy.contains('Save and continue').click()
    cy.get('[name="archive_audit_retest_disproportionate_burden_state"]').check('no-claim')
    cy.get('[name="archive_audit_retest_disproportionate_burden_notes"]').clear().type(disproportionateNote)
    cy.get('[name="archive_audit_retest_statement_2_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('12-week test').click()
  })

  it('can edit 12-week accessibility statement compliance decision', () => {
    cy.get('#edit-audit-retest-statement-decision').click()
    cy.get('[name="case-compliance-statement_compliance_state_12_week"]').check('compliant')
    cy.get('[name="case-compliance-statement_compliance_notes_12_week"]').clear().type(statementComplianceNote)
    cy.get('[name="audit_retest_statement_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('12-week test').click()
    cy.contains(statementComplianceNote)
  })
})
