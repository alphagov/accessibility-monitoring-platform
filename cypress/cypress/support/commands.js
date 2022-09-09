/* global cy Cypress */

const username = 'auditor@email.com'
const password = 'secret'

Cypress.Commands.add('login', () => {
  cy.visit('/account/login/')
  cy.get('input[name="auth-username"]').type(username)
  cy.get('input[name="auth-password"]').type(password)
  cy.get('form').submit()
  cy.getCookie('sessionid').should('exist')
})
