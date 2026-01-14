/* global cy before Cypress */

const newOrganisationName = 'New detailed organisation name'
const newDomain = 'detailed-org.com'
const newHomePageURL = `https://${newDomain}`

describe('Create detailed case', () => {
  before(() => {
    cy.login()
  })

  it('can follow case lifecycle', () => {
    cy.visit('/cases')

    cy.title().should('eq', 'Search cases')
    cy.contains('Filter and options').click()
    cy.contains('Create detailed case').click()

    cy.title().should('eq', 'Create detailed case')
    cy.get('#id_home_page_url').type(newHomePageURL)
    cy.get('#id_organisation_name').type(newOrganisationName)
    cy.get('#id_sector').select('Private Sector Business')
    cy.get('[name="enforcement_body"]').check('ehrc')
    cy.get('[name="psb_location"]').check('england')
    cy.contains('Save and continue case').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Case metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Contact details`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Information request`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Testing`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Testing outcome`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Report ready for QA`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | QA auditor`)
    cy.get('#id_reviewer').select('QA Auditor')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | QA comments (0)`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | QA approval`)
    cy.get('[name="report_approved_status"]').check('yes')
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Final report`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Report sent`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | 12-week deadline`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Report acknowledged`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | 12-week update requested`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | 12-week update received`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Retest result`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Compliance decisions`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Recommendation`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Closing the case`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Statement enforcement`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Equality body metadata`)
    cy.contains('Save and continue').click()

    cy.title().should('eq', `${newDomain} · ${newOrganisationName} | Detailed case overview`)
  })
})
