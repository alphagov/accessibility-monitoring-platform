/* global cy before Cypress */

const newOrganisationName = 'New mobile organisation name'
const newHomePageURL = 'https://mobile-org.com'

describe('Create mobile case', () => {
  before(() => {
    cy.login()
  })

  it('can follow case lifecycle', () => {
    cy.visit('/cases')

    cy.title().should('eq', 'Search cases')
    cy.contains('Create mobile case').click()

    cy.title().should('eq', 'Create mobile case')
    cy.get('#id_home_page_url').type(newHomePageURL)
    cy.get('#id_organisation_name').type(newOrganisationName)
    cy.get('#id_sector').select('Private Sector Business')
    cy.contains('Save and continue case').click()

    cy.title().should('eq', `${newOrganisationName} | Case metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Contact details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Information request`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Auditor`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | iOS details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | iOS outcome`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Android details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Android outcome`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Reports ready for QA`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | QA auditor`)
    cy.get('#id_reviewer').select('QA Auditor')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | QA comments`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | QA approval`)
    cy.get('[name="report_approved_status"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Final reports`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Reports sent`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week deadline`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Reports acknowledged`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week update requested`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | 12-week update received`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | iOS retesting`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | iOS retest result`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Android retesting`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Android retest result`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Recommendation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Closing the case`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Statement enforcement`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Equality body metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newOrganisationName} | Mobile case overview`)
  })
})
