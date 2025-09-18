/* global cy */

const username = 'auditor@email.com'
const password = 'secret'

describe('Login', () => {
  it('can see dashboard page', () => {
    cy.visit('/account/login/')
    cy.get('input[name="auth-username"]').type(username)
    cy.get('input[name="auth-password"]').type(password)
    cy.get('form[data-cy="login-form"]').submit()
    cy.getCookie('sessionid').should('exist')
    cy.getCookie('csrftoken').should('exist')
    cy.visit('/')
    cy.title().should('eq', 'Home | Dashboard')
  })
})
