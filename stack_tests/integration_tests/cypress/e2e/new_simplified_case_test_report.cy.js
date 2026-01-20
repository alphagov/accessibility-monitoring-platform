/* global cy before Cypress */

const newOrganisationName = 'New simplified organisation name'
const newDomain = 'simplified-org.com'
const newHomePageURL = `https://${newDomain}`
const newAccessibilityStatementURL = `${newHomePageURL}/accessibility-statement`

describe('Create simplified case, tests and report', () => {
  before(() => {
    cy.login()
  })

  it('can follow case lifecycle', () => {
    cy.visit('/cases')

    cy.title().should('eq', 'Search cases')
    cy.contains('Filter and options').click()
    cy.contains('Create simplified case').click()

    cy.title().should('eq', 'Create simplified case')
    cy.get('#id_organisation_name').type(newOrganisationName)
    cy.get('#id_home_page_url').type(newHomePageURL)
    cy.get('[name="enforcement_body"]').check('ehrc')
    cy.get('[name="psb_location"]').check('england')
    cy.get('#id_psb_location_0').click()
    cy.get('#id_sector').select('Private Sector Business')
    cy.contains('Save and continue case').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Case metadata`)
    cy.get('#id_auditor').select('Auditor')
    cy.get('#id_enforcement_body_0').click()
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Testing details`)
    cy.contains('This case does not have a test. Click Start test to begin.')
    cy.contains('.govuk-button', 'Start test').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Initial test metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Add or remove pages`)
    cy.get('[name="standard-1-not_found"]').check()
    cy.get('[name="standard-4-url').type(newAccessibilityStatementURL)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Home page test`)
    cy.get('[name="form-0-check_result_state"]').check('error')
    cy.get('[name="form-0-notes').type('Hi, I am an error')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Accessibility statement page test`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Compliance decision`)
    cy.get('[name="case-compliance-website_compliance_state_initial"]').check('partially-compliant')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | WCAG summary`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement links`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement overview`)
    cy.get('[name="form-0-check_result_state"]').check('yes')
    cy.get('[name="form-1-check_result_state"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement information`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Compliance status`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Non-accessible content`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement preparation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Feedback and enforcement procedure`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Disproportionate burden claim`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Custom issues`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Disproportionate burden`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement compliance`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement summary`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Start report`)
    cy.contains('This case currently does not have a report.')
    cy.contains('.govuk-button', 'Start report').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Report ready for QA`)
    cy.get('[name="report_review_status"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | QA auditor`)
    cy.get('#id_reviewer').select('QA Auditor')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | QA comments (0)`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | QA approval`)
    cy.get('[name="report_approved_status"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Publish report`)
    cy.contains('.govuk-button', 'Publish report').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Publish report`)
    cy.contains('HTML report successfully created!')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Manage contact details`)
    cy.contains('start correspondence process').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Request contact details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | One-week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Four-week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Report sent on`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | One week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Four week follow-up`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Report acknowledged`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | 12-week update requested`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | One week follow-up for 12-week update`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | 12-week update request acknowledged`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Start 12-week retest`)
    cy.contains('This case does not have a retest. Click Start retest to move to the testing environment.')
    cy.contains('.govuk-button', 'Start retest').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | 12-week retest metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Update page links`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Home page retest`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Compliance decision`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | WCAG summary`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement links`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement overview`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement information`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Compliance status`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Non-accessible content`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement preparation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Feedback and enforcement procedure`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Disproportionate burden claim`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Custom issues`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Disproportionate burden`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Compliance decision`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement summary`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Reviewing changes`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Recommendation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Closing the case`)
    cy.contains('Save and continue').click()

    cy.contains('Post case').click()
    cy.contains('Retest overview').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Retest overview`)
    cy.contains('New retest').click()

    cy.title().should('eq', 'Retest #1 | Retest metadata')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Retest #1 | Home`)
    cy.contains('Save and next page').click()

    cy.title().should('eq', 'Retest #1 | Comparison')
    cy.contains('Save and continue').click()

    cy.title().should('eq', 'Retest #1 | Compliance decision')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement links`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement overview`)
    cy.get('[name="form-0-check_result_state"]').check('yes')
    cy.get('[name="form-1-check_result_state"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement information`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Compliance status`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Non-accessible content`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement preparation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Feedback and enforcement procedure`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Disproportionate burden claim`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Custom statement issues`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement results`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Disproportionate burden`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement decision`)
    cy.contains('Save and exit').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Retest overview`)
  })
})
