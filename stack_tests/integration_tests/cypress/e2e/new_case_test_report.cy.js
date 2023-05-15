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

    cy.title().should('eq', `${newOrganisationName} | Case details`)
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
    cy.get('[name="standard-2-url').type(newAccessibilityStatementURL)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Testing Home`)
    cy.get('[name="form-0-check_result_state"]').check('error')
    cy.get('[name="form-0-notes').type('Hi, I am an error')
    cy.contains('Save and next page').click()

    cy.title().should('eq', `${newOrganisationName} | Testing Accessibility statement`)
    cy.contains('Save and next page').click()

    cy.title().should('eq', `${newOrganisationName} | Website compliance decision`)
    cy.get('[name="case-is_website_compliant"]').check('not-compliant')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Accessibility statement Pt. 1`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Accessibility statement Pt. 2`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Accessibility statement compliance decision`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Report options`)
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
    cy.contains('Go to QA process').click()

    cy.title().should('eq', `${newOrganisationName} | QA process`)
    cy.get('[name="report_review_status"]').check('yes')
    cy.get('#id_reviewer').select('QA Auditor')
    cy.get('[name="report_approved_status"]').check('yes')
    cy.contains('Save').click()

    cy.contains('Report details').click()
    cy.contains('Go to Case > Report publisher').click()

    cy.title().should('eq', `${newOrganisationName} | Report publisher`)
    cy.contains('The report has been approved and is ready to be published')
    cy.contains('Publish HTML report').click()

    cy.title().should('eq', `${newOrganisationName} | Publish report`)
    cy.contains('Create HTML report').click()

    cy.title().should('eq', `${newOrganisationName} | Report publisher`)
    cy.contains('HTML report successfully created!')
    cy.contains('final HTML report')

    cy.contains('Case').click()
    cy.contains('View case').click()
    cy.get('#edit-report-details').click()

    cy.title().should('eq', `${newOrganisationName} | Report details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | QA process`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Contact details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Report correspondence`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week correspondence`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week retest`)
    cy.contains('This case does not have a retest. Click Start retest to move to the testing environment.')
    cy.contains('.govuk-button', 'Start retest').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week test metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Retesting Home`)
    cy.contains('Save and next page').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week pages comparison`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week website compliance decision`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week accessibility statement Pt. 1`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week accessibility statement Pt. 2`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week accessibility statement comparison`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week accessibility statement compliance decision`)
    cy.contains('Save and exit').click()

    cy.title().should('eq', `${newOrganisationName} | View 12-week test`)
    cy.contains('Case').click()
    cy.get('#edit-twelve-week-retest').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week retest`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Reviewing changes`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Closing the case`)
    cy.contains('Save and continue').click()
  })
})
