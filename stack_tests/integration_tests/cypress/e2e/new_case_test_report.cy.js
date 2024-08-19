/* global cy before Cypress */

const newOrganisationName = 'New organisation name'
const newHomePageURL = 'https://example.com'
const newAccessibilityStatementURL = `${newHomePageURL}/accessibility-statement`

describe('Create case, tests and report', () => {
  before(() => {
    cy.login()
  })

  it('can follow case lifecycle', () => {
    cy.visit('/cases')

    cy.title().should('eq', 'Search')
    cy.contains('Create case').click()

    cy.title().should('eq', 'Create case')
    cy.get('#id_organisation_name').type(newOrganisationName)
    cy.get('#id_home_page_url').type(newHomePageURL)
    cy.get('[name="enforcement_body"]').check('ehrc')
    cy.get('[name="psb_location"]').check('england')
    cy.get('#id_psb_location_0').click()
    cy.get('#id_sector').select('Private Sector Business')
    cy.contains('Save and continue case').click()

    cy.title().should('eq', 'Create case')
    cy.contains('We have found 1 cases matching the details you have given')
    cy.contains('Save and continue case').click()

    cy.title().should('eq', `${newOrganisationName} | Case metadata`)
    cy.get('#id_auditor').select('Auditor')
    cy.get('#id_enforcement_body_0').click()
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Testing details`)
    cy.contains('This case does not have a test. Click Start test to move to the testing environment.')
    cy.contains('.govuk-button', 'Start test').click()

    cy.title().should('eq', `${newOrganisationName} | Test metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Pages`)
    cy.get('[name="standard-1-not_found"]').check()
    cy.get('[name="standard-4-url').type(newAccessibilityStatementURL)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Home page test`)
    cy.get('[name="form-0-check_result_state"]').check('error')
    cy.get('[name="form-0-notes').type('Hi, I am an error')
    cy.contains('Save and next page').click()

    cy.title().should('eq', `${newOrganisationName} | Accessibility statement page test`)
    cy.contains('Save and next page').click()

    cy.title().should('eq', `${newOrganisationName} | Website compliance decision`)
    cy.get('[name="case-compliance-website_compliance_state_initial"]').check('partially-compliant')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Statement links`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Statement overview`)
    cy.get('[name="form-0-check_result_state"]').check('yes')
    cy.get('[name="form-1-check_result_state"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Statement information`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Compliance status`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Non-accessible content`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Statement preparation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Feedback and enforcement procedure`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Custom statement issues`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Initial disproportionate burden claim`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Initial statement compliance decision`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Test summary`)
    cy.contains('Save and exit').click()

    cy.title().should('eq', `${newOrganisationName} | Testing details`)
    cy.contains('Case').click()

    cy.title().should('eq', `${newOrganisationName} | View case`)
    cy.get('#edit-report-details').click()

    cy.title().should('eq', `${newOrganisationName} | Report details`)
    cy.contains('This case currently does not have a report.')
    cy.contains('Create report').click()

    cy.title().should('eq', `${newOrganisationName} | Report publisher`)
    cy.contains('Mark the report as ready to review')
    cy.contains('Go to Report details').click()

    cy.title().should('eq', `${newOrganisationName} | Report details`)
    cy.get('[name="report_review_status"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | QA comments`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Report approved`)
    cy.get('#id_reviewer').select('QA Auditor')
    cy.get('[name="report_approved_status"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Publish report`)
    cy.contains('Create HTML report').click()

    cy.title().should('eq', `${newOrganisationName} | Publish report`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Manage contact details`)
    cy.contains('start correspondence process').click()

    cy.title().should('eq', `${newOrganisationName} | Request contact details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | One-week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Four-week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Unresponsive PSB`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Report sent on`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | One week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Four week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Report acknowledged`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week update requested`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | One week follow-up for final update`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week update request acknowledged`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week retest`)
    cy.contains('This case does not have a retest. Click Start retest to move to the testing environment.')
    cy.contains('.govuk-button', 'Start retest').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week retest metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Retesting Home`)
    cy.contains('Save and next page').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week pages comparison`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week website compliance decision`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week statement links`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week statement overview`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week statement information`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week compliance status`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week non-accessible content`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week statement preparation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week feedback and enforcement procedure`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week custom statement issues`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week disproportionate burden claim`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week statement compliance decision`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week accessibility statement comparison`)
    cy.contains('Save and exit').click()

    cy.title().should('eq', `${newOrganisationName} | View 12-week retest`)
    cy.contains('Case').click()
    cy.get('#edit-twelve-week-retest').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week retest`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Reviewing changes`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Enforcement recommendation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Closing the case`)
    cy.contains('Save and continue').click()
  })
})
