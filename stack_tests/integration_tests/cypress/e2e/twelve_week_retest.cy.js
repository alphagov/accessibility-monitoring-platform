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
    cy.contains(/^12-week retest metadata$/).click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="audit_retest_metadata_notes"]').clear().type(retestMetadataNote)
    cy.get('[name="audit_retest_metadata_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', 'ExampleCorp | Case overview')
    cy.contains(retestMetadataNote)
  })

  it('can edit 12-week retesting home', () => {
    cy.contains('12-week WCAG test').click()
    cy.contains(/^Home page retest$/).click()
    cy.title().should('eq', 'ExampleCorp | Home page retest')
    cy.get('[name="form-0-retest_state"]').check('fixed')
    cy.get('[name="form-0-retest_notes"]').clear().type(retestErrorText)
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', 'ExampleCorp | Case overview')
    cy.contains(retestErrorText)
  })
})
