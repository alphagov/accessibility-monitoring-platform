/* global cy before Cypress */

const retestMetadataNote = '12-week retest metadata note'
const retestErrorText = 'Retest error note'
const websiteComplianceNote = 'Website compliance note'
const scopeNote = 'Accessibility statement scope note'
const disproportionateNote = 'Disproportionate burden note'
const statementComplianceNote = 'Accessibility statement compliance note'

describe('View test', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
    cy.visit('/audits/1/audit-retest-detail')
  })

  it('can edit 12-week test metadata', () => {
    cy.contains('a', 'Edit 12-week test metadata').click()
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
    cy.contains('a', 'Edit 12-week pages comparison').click()
    cy.get('[name="audit_retest_pages_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week website compliance decision', () => {
    cy.contains('a', 'Edit 12-week website compliance decision').click()
    cy.get('[name="case-website_state_final"]').check('compliant')
    cy.get('[name="case-website_state_notes_final"]').clear().type(websiteComplianceNote)
    cy.get('[name="audit_retest_website_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('12-week test').click()
    cy.contains(websiteComplianceNote)
  })

  it('can edit 12-week accessibility statement', () => {
    cy.contains('a', 'Edit 12-week accessibility statement').click()
    cy.get('[name="audit_retest_scope_state"]').check('present')
    cy.get('[name="audit_retest_scope_notes"]').clear().type(scopeNote)
    cy.get('[name="audit_retest_statement_1_complete_date"]').click()
    cy.contains('Save and continue').click()
    cy.get('[name="audit_retest_disproportionate_burden_state"]').check('no-claim')
    cy.get('[name="audit_retest_disproportionate_burden_notes"]').clear().type(disproportionateNote)
    cy.get('[name="audit_retest_statement_2_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('12-week test').click()
    cy.contains(scopeNote)
    cy.contains(disproportionateNote)
  })

  it('can edit 12-week accessibility statement compliance decision', () => {
    cy.contains('a', 'Edit 12-week accessibility statement compliance decision').click()
    cy.get('[name="case-accessibility_statement_state_final"]').check('compliant')
    cy.get('[name="case-accessibility_statement_notes_final"]').clear().type(statementComplianceNote)
    cy.get('[name="audit_retest_statement_decision_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('12-week test').click()
    cy.contains(statementComplianceNote)
  })
})
