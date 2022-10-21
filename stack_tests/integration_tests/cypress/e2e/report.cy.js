/* global cy before after Cypress */

const metadataNote = 'Report metadata note content'
const reportIntroduction = 'Alternate report introduction content'
const reportHowAccessible = 'Alternate how accessible the website is content'
const reportHowWeChecked = 'Alternate how we checked content'
const reportPagesWeChecked = 'Alternate pages we checked content'
const reportIssuesWeFound = 'Alternate the issues we found content'
const reportHomePage = 'Alternate home page content'
const newIssueDescription = 'New issue description'
const newIssueWhereFound = 'New issue where found'

describe('Report publisher', () => {
  before(() => {
    cy.login()
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid')
    cy.visit('/reports/1/report-publisher')
  })

  it('contains link to latest published HTML report', () => {
    cy.contains('latest published HTML report')
      .should('have.attr', 'href')
      .then((href) => {
        expect(href).to.include('/reports/96b1afce-a445-42c3-961c-7708aba196f3')
      })
  })

  describe('Edit report', () => {
    beforeEach(() => {
      cy.contains('a', 'Edit report').click()
    })

    after(() => {
      cy.contains('a', 'Reset report').click()
      cy.title().should('eq', 'ExampleCorp | Reset report')
      cy.contains('a', 'Reset report').click()
      cy.title().should('eq', 'ExampleCorp | Edit report')
    })

    it('can edit report metadata', () => {
      cy.get('a[data-cy="edit-report-link"]').eq(0).click()
      cy.title().should('eq', 'ExampleCorp | Report metadata')
      cy.get('[name="notes"]').clear().type(metadataNote)
      cy.contains('Save and return to report view').click()
      cy.contains(metadataNote)
    })

    it('can edit report introduction', () => {
      cy.get('a[data-cy="edit-report-link"]').eq(1).click()
      cy.title().should('eq', 'ExampleCorp | Introduction')
      cy.get('[name="content"]').clear().type(reportIntroduction)
      cy.contains('Save and return to report view').click()
      cy.contains(reportIntroduction)
    })

    it('can edit how accessible the website is', () => {
      cy.get('a[data-cy="edit-report-link"]').eq(2).click()
      cy.title().should('eq', 'ExampleCorp | How accessible the website is')
      cy.get('[name="content"]').clear().type(reportHowAccessible)
      cy.contains('Save and return to report view').click()
      cy.contains(reportHowAccessible)
    })

    it('can edit how we checked', () => {
      cy.get('a[data-cy="edit-report-link"]').eq(3).click()
      cy.title().should('eq', 'ExampleCorp | How we checked')
      cy.get('[name="content"]').clear().type(reportHowWeChecked)
      cy.contains('Save and return to report view').click()
      cy.contains(reportHowWeChecked)
    })

    it('can edit pages we checked', () => {
      cy.get('a[data-cy="edit-report-link"]').eq(4).click()
      cy.title().should('eq', 'ExampleCorp | Pages we checked')
      cy.get('[name="form-0-cell_content_1"]').clear().type(reportPagesWeChecked)
      cy.contains('Move row up').click()
      cy.contains('Save and return to report view').click()
      cy.contains(reportPagesWeChecked)
    })

    it('can edit the issues we found', () => {
      cy.get('a[data-cy="edit-report-link"]').eq(5).click()
      cy.title().should('eq', 'ExampleCorp | The issues we found')
      cy.get('[name="content"]').clear().type(reportIssuesWeFound)
      cy.contains('Save and return to report view').click()
      cy.contains(reportIssuesWeFound)
    })

    it('can edit home page issues', () => {
      cy.get('a[data-cy="edit-report-link"]').eq(6).click()
      cy.title().should('eq', 'ExampleCorp | Home page issues')
      cy.get('[name="content"]').clear().type(reportHomePage)
      cy.contains('Add row').click()
      cy.get('[name="form-1-cell_content_1"]').clear().type(newIssueDescription)
      cy.get('[name="form-1-cell_content_2"]').clear().type(newIssueWhereFound)
      cy.contains('Save and return to report view').click()
      cy.contains(reportHomePage)
      cy.contains(newIssueDescription)
      cy.contains(newIssueWhereFound)
    })
  })
})
