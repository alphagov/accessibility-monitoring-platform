/* global cy before after Cypress */

const metadataNote = 'Report note content'
const reportIntroduction = 'Alternate report introduction content'
const reportHowAccessible = 'Alternate how accessible the website is content'
const reportHowWeChecked = 'Alternate how we checked content'
const reportPagesWeChecked = 'Alternate page name'
const reportIssuesWeFound = 'Alternate the issues we found content'
const reportHomePage = 'Alternate home page content'
const newIssueDescription = 'New issue description'
const newIssueWhereFound = 'New issue where found'

describe('Report publisher', () => {
  beforeEach(() => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    cy.visit('/reports/1/report-publisher')
  })

  it('contains link to latest published HTML report', () => {
    cy.contains('published HTML report')
      .should('have.attr', 'href')
      .then((href) => {
        expect(href).to.include('/reports/96b1afce-a445-42c3-961c-7708aba196f3')
      })
  })

  it('can edit report notes', () => {
    cy.contains('Edit notes').click()
    cy.title().should('eq', 'ExampleCorp | Report notes')
    cy.get('[name="notes"]').clear().type(metadataNote)
    cy.contains('Save and return to report publisher').click()
    cy.contains(metadataNote)
  })

  it('can edit how accessible the website is', () => {
    cy.contains('Edit test > Website compliance decision').click()
    cy.title().should('eq', 'ExampleCorp | Website compliance decision')
    cy.get('[name="case-compliance-website_compliance_state_initial"]').check('partially-compliant')
    cy.contains('Save').click()
    cy.visit('/reports/1/report-publisher')
    cy.contains('Based on our testing, this site is partially compliant')
  })

  it('can edit pages we checked', () => {
    cy.contains('Edit test > Pages').click()
    cy.title().should('eq', 'ExampleCorp | Add or remove pages')
  })

  it('can edit home page issues', () => {
    cy.contains('Edit test > Home').click()
    cy.title().should('eq', 'ExampleCorp | Home page test')
  })

  it('can edit report options', () => {
    cy.contains('Edit test > Report options').click()
    cy.title().should('eq', 'ExampleCorp | Report options')
  })
})
