/* global cy before Cypress */

const organisationName = 'Simplified Organisation'
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

describe('Case overview', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/simplified/1/view')
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
    cy.contains(/^Case metadata$/).click()
    cy.get('#id_auditor').select('Auditor')
    cy.get('[name="psb_location"]').check('uk_wide')
    cy.get('[name="notes"]').clear().type(caseDetailsNote)
    cy.get('[name="case_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.title().should('eq', `example.com · ${organisationName} | Simplified case overview`)
    cy.contains(caseDetailsNote)
  })

  it('can edit test metadata', () => {
    cy.contains('Initial WCAG test').click()
    cy.contains(/^Initial test metadata$/).click()
    cy.get('[name="audit_metadata_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit QA auditor', () => {
    cy.contains(/^ Report QA/).click()
    cy.contains(/^QA auditor$/).click()
    cy.get('#id_reviewer').select('QA Auditor')
    cy.get('[name="qa_auditor_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit QA comments', () => {
    cy.contains(/^ Report QA/).click()
    cy.contains(/^QA comments \(0\)$/).click()
    cy.get('[name="body"]').clear().type(qaComment)
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.contains(qaComment)
  })

  it('can edit Report approved', () => {
    cy.contains(/^ Report QA/).click()
    cy.contains(/^QA approval$/).click()
    cy.get('[name="qa_approval_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit contact details', () => {
    cy.contains('Contact details').click()
    cy.contains(/^Manage contact details$/).click()
    cy.get('a')
      .not('details a')
      .filter(':visible')
      .filter((_, el) => /(^|\b)Edit(\b|\/)/i.test(el.textContent))
      .last()
      .scrollIntoView({ block: 'center' })
      .click();
    cy.get('[name="name"]').clear().type(contactName)
    cy.get('[name="email"]').clear().type(contactEmail)
    cy.contains('Save and return').click()
    cy.get('[name="manage_contact_details_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.contains(contactName)
    cy.contains(contactEmail)
  })

  it('can edit 12-week retest metadata', () => {
    cy.contains('12-week WCAG test').click()
    cy.contains(/^12-week retest metadata$/).click()
    cy.get('[name="audit_retest_metadata_complete_date"]').click()
    cy.contains('Save').click()
  })

  it('can edit reviewing changes', () => {
    cy.contains('Closing the case').click()
    cy.contains(/^Reviewing changes$/).click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="psb_progress_notes"]').clear().type(psbProgressNote)
    cy.get('[name="is_ready_for_final_decision"]').check('yes')
    cy.get('[name="review_changes_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.contains(psbProgressNote)
  })

  it('can edit enforcement recommendation', () => {
    cy.contains('Closing the case').click()
    cy.contains(/^Recommendation$/).click()
    cy.contains('Populate with today\'s date').click()
    cy.get('[name="recommendation_for_enforcement"]').check('no-further-action')
    cy.get('[name="recommendation_notes"]').clear().type(recommendationNote)
    cy.get('[name="enforcement_recommendation_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.contains(recommendationNote)
  })

  it('can edit closing the case', () => {
    cy.contains('Closing the case').click()
    cy.contains(/^Closing the case$/).click()
    cy.get('[name="case_completed"]').check('complete-send')
    cy.get('[name="case_close_complete_date"]').click()
    cy.contains('Save').click()
    cy.contains('li', /#S-1\b/).click()
    cy.contains(recommendationNote)
  })

  it('can reach statement enforcement', () => {
    cy.get('details').contains('Post case').click()
    cy.contains(/^Statement enforcement$/).click()
    cy.title().should('eq', `example.com · ${organisationName} | Statement enforcement`)
  })
})
