/* global cy */

const username = 'admin@email.com'
const password = 'password'

describe('Login', () => {
  it('Can login through the UI', function () {
    cy.visit('/account/login/')
    cy.get('input[name="auth-username"]').type(username)
    cy.get('input[name="auth-password"]').type(password)
    cy.get('form').submit()
    cy.getCookie('sessionid').should('exist')
  })
})
