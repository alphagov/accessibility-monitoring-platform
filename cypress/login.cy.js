/* global cy before Cypress */

const username = 'auditor@email.com'
const password = 'secret'

describe('Login and visit pages', () => {
  before(() => {
    cy.visit('/account/login/')
    cy.get('input[name="auth-username"]').type(username)
    cy.get('input[name="auth-password"]').type(password)
    cy.get('form').submit()
    cy.getCookie('sessionid').should('exist')
    cy.getCookie('csrftoken').should('exist')
  })

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid', 'csrftoken')
  })

  it('can see dashboard page', () => {
    cy.visit('/')
    cy.title().should('eq', 'Dashboard | Your cases')
  })

  it('can seee search page', () => {
    cy.visit('/cases/')
    cy.title().should('eq', 'Search')
  })
})
