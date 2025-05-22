/* global cy, Cypress */

describe('Login', () => {
  it('can see home page', () => {
    cy.visit('/account/login/')
    cy.get('input[name="auth-username"]').type(Cypress.env('SMOKE_TESTS_USERNAME'))
    cy.get('input[name="auth-password"]').type(Cypress.env('SMOKE_TESTS_PASSWORD'))
    cy.get('form[data-cy="login-form"]').submit()
    cy.getCookie('sessionid').should('exist')
    cy.getCookie('csrftoken').should('exist')
    cy.title().should('eq', 'Home | Your simplified cases')
  })
})
