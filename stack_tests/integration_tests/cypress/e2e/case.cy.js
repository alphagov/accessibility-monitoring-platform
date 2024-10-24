/* global cy before Cypress */

const organisationName = 'ExampleCorp'
const caseDetailsNote = 'Case details note'
const qaComment = 'QA comment'
const contactName = 'Example Contact 2'
const contactEmail = 'example2@example.com'
const zendeskUrl = 'https://zendesk.com/url'
const correspondenceNote = 'Correspondence note'
const twelveWeekCorrespondenceNote = '12-week correspondence note'
const psbProgressNote = 'PSB progress note'
const recommendationNote = 'Recommendation note'
const equalityBodyCorrespondenceNote = 'Equality body correspondence note'
const postCaseNote = 'Post case note'
const psbAppealNote = 'PSB appeal note'
const zenUrl = 'https://zendesk.com/ticket'
const zenSummary = 'Zendesk ticket summary'

describe('View case', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/cases/1/view')
  })

  it('can search within case', () => {
    cy.get('[name="search_in_case"]').clear().type('report sent')
    cy.contains('Found 1 result for report sent')
    cy.contains('Report sent')
    cy.get('[name="search_in_case"]').clear()
    cy.contains('Found 1 result for report sent').should('not.exist')
  })

  it('can edit case details', () => {
    cy.contains('Case details').click()
    cy.get('#edit-cases1edit-case-metadata').click()
    cy.get('#id_auditor').select('Auditor')
    cy.get('[name="psb_location"]').check('uk_wide')
    cy.get('[name="notes"]').clear().type(caseDetailsNote)
    cy.get('[name="case_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.title().should('eq', `${organisationName} | View case`)
    cy.contains(caseDetailsNote)
  })

  it('can edit test metadata', () => {
    cy.contains('Initial WCAG test').click()
    cy.get('#edit-audits1edit-audit-metadata').click()
    cy.get('[name="audit_metadata_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit QA auditor', () => {
    cy.contains(/^ Report QA/).click()
    cy.get('#edit-cases1edit-qa-auditor').click()
    cy.get('#id_reviewer').select('QA Auditor')
    cy.get('[name="qa_auditor_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit QA comments', () => {
    cy.contains(/^ Report QA/).click()
    cy.get('#edit-cases1edit-qa-comments').click()
    cy.get('[name="body"]').clear().type(qaComment)
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.contains(qaComment)
  })

  it('can edit Report approved', () => {
    cy.contains(/^ Report QA/).click()
    cy.get('#edit-cases1edit-qa-approval').click()
    cy.get('[name="qa_approval_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit contact details', () => {
    cy.contains('Contact details').click()
    cy.get('#edit-cases1manage-contact-details').click()
    cy.contains('Edit or remove').click()
    cy.get('[name="name"]').clear().type(contactName)
    cy.get('[name="email"]').clear().type(contactEmail)
    cy.contains('Save and return').click()
    cy.get('[name="manage_contact_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.contains(contactName)
    cy.contains(contactEmail)
  })

  it('can edit 12-week retest metadata', () => {
    cy.contains('12-week WCAG test').click()
    cy.get('#edit-audits1edit-audit-retest-metadata').click()
    cy.get('[name="audit_retest_metadata_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week retest WCAG test summary', () => {
    cy.contains('12-week WCAG test').click()
    cy.get('#edit-audits1edit-retest-wcag-summary').click()
    cy.get('[name="audit_retest_wcag_summary_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week retest statement links', () => {
    cy.contains('12-week statement').click()
    cy.get('#edit-audits1edit-audit-retest-statement-pages').click()
    cy.get('[name="audit_retest_statement_pages_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week retest statement overview', () => {
    cy.contains('12-week statement').click()
    cy.get('#edit-audits1edit-retest-statement-overview').click()
    cy.get('[name="audit_retest_statement_overview_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week retest statement information', () => {
    cy.contains('12-week statement').click()
    cy.get('#edit-audits1edit-retest-statement-website').click()
    cy.get('[name="audit_retest_statement_website_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week retest disproportionate burden', () => {
    cy.contains('12-week statement').click()
    cy.get('#edit-audits1edit-twelve-week-disproportionate-burden').click()
    cy.get('[name="twelve_week_disproportionate_burden_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit 12-week retest statement test summary', () => {
    cy.contains('12-week statement').click()
    cy.get('#edit-audits1edit-retest-statement-summary').click()
    cy.get('[name="audit_retest_statement_summary_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit reviewing changes', () => {
    cy.contains('Closing the case').click()
    cy.get('#edit-cases1edit-review-changes').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="psb_progress_notes"]').clear().type(psbProgressNote)
    cy.get('[name="is_ready_for_final_decision"]').check('yes')
    cy.get('[name="review_changes_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.contains(psbProgressNote)
  })

  it('can edit enforcement recommendation', () => {
    cy.contains('Closing the case').click()
    cy.get('#edit-cases1edit-enforcement-recommendation').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="recommendation_for_enforcement"]').check('no-further-action')
    cy.get('[name="recommendation_notes"]').clear().type(recommendationNote)
    cy.get('[name="enforcement_recommendation_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.contains(recommendationNote)
  })

  it('can edit closing the case', () => {
    cy.contains('Closing the case').click()
    cy.get('#edit-cases1edit-case-close').click()
    cy.get('[name="case_completed"]').check('complete-send')
    cy.get('[name="case_close_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains(/^Case$/).click()
    cy.contains(recommendationNote)
  })

  it('can reach statement enforcement', () => {
    cy.contains('Post case (0/0)').click()
    cy.get('#edit-cases1statement-enforcement').click()
    cy.title().should('eq', `${organisationName} | Statement enforcement`)
  })
})
