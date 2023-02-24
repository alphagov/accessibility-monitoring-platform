/* global cy before Cypress */

const organisationName = 'ExampleCorp'
const caseDetailsNote = 'Case details note'
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

describe('View case', () => {
  beforeEach(() => {
    cy.session('login', cy.login, {cacheAcrossSpecs: true})
    cy.visit('/cases/1/view')
  })

  it('can edit case details', () => {
    cy.contains('a', 'Edit case details').click()
    cy.get('#id_auditor').select('Auditor')
    cy.get('[name="psb_location"]').check('uk_wide')
    cy.get('[name="notes"]').clear().type(caseDetailsNote)
    cy.get('[name="case_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.title().should('eq', `${organisationName} | View case`)
    cy.contains(caseDetailsNote)
  })

  it('can edit testing details', () => {
    cy.contains('a', 'Edit testing details').click()
    cy.get('[name="testing_details_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit report details', () => {
    cy.contains('a', 'Edit report details').click()
    cy.get('[name="reporting_details_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit QA process', () => {
    cy.contains('a', 'Edit QA process').click()
    cy.get('[name="report_review_status"]').check('ready-to-review')
    cy.get('#id_reviewer').select('QA Auditor')
    cy.get('[name="qa_process_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
  })

  it('can edit contact details', () => {
    cy.contains('a', 'Edit contact details').click()
    cy.get('[name="form-0-name"]').clear().type(contactName)
    cy.get('[name="form-0-email"]').clear().type(contactEmail)
    cy.get('[name="contact_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.contains(contactName)
    cy.contains(contactEmail)
  })

  it('can edit report correspondence', () => {
    cy.contains('a', 'Edit report correspondence').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="report_followup_week_1_sent_date"]').click()
    cy.get('[name="report_followup_week_4_sent_date"]').click()
    cy.get('[name="zendesk_url"]').clear().type(zendeskUrl)
    cy.get('[name="correspondence_notes"]').clear().type(correspondenceNote)
    cy.get('[name="report_correspondence_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.contains(zendeskUrl)
    cy.contains(correspondenceNote)
  })

  it('can edit 12-week correspondence', () => {
    cy.contains('a', 'Edit 12-week correspondence').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="twelve_week_1_week_chaser_sent_date"]').click()
    cy.get('[name="twelve_week_correspondence_notes"]').clear().type(twelveWeekCorrespondenceNote)
    cy.get('[name="twelve_week_response_state"]').check('no')
    cy.get('[name="twelve_week_correspondence_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.contains(twelveWeekCorrespondenceNote)
  })

  it('can edit 12-week retest', () => {
    cy.contains('a', 'Edit 12-week retest').click()
    cy.get('[name="twelve_week_retest_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit reviewing changes', () => {
    cy.contains('a', 'Edit reviewing changes').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="psb_progress_notes"]').clear().type(psbProgressNote)
    cy.get('[name="is_ready_for_final_decision"]').check('yes')
    cy.get('[name="review_changes_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.contains(psbProgressNote)
  })

  it('can edit closing the case', () => {
    cy.contains('a', 'Edit closing the case').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="recommendation_for_enforcement"]').check('no-further-action')
    cy.get('[name="recommendation_notes"]').clear().type(recommendationNote)
    cy.get('[name="case_completed"]').check('complete-send')
    cy.get('[name="case_close_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.contains(recommendationNote)
  })

  it('can edit equality body summary', () => {
    cy.contains('a', 'Edit equality body summary').click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="enforcement_body_pursuing"]').check('yes-completed')
    cy.get('[name="enforcement_body_correspondence_notes"]').clear().type(equalityBodyCorrespondenceNote)
    cy.get('[name="enforcement_correspondence_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.contains(equalityBodyCorrespondenceNote)
  })

  it('can edit post case summary', () => {
    cy.contains('a', 'Edit post case summary').click()
    cy.get('[name="post_case_notes"]').clear().type(postCaseNote)
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="psb_appeal_notes"]').clear().type(psbAppealNote)
    cy.get('[name="post_case_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('Case').click()
    cy.contains(postCaseNote)
    cy.contains(psbAppealNote)
  })

  it('can see status workflow page', () => {
    cy.contains('a', 'Edit post case summary').click()
    cy.contains('View status workflow').click()
    cy.title().should('eq', `${organisationName} | Status workflow`)
  })
})
