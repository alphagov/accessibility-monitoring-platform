/* global cy before */

describe('Login', () => {
  before(() => {
    cy.fixture('users.json').as('mockedUsers')
  })

  it('Can login through the UI', function () {
    cy.visit('/account/login/')
    cy.get('input[name="username"]').type(this.mockedUsers[0].fields.email)
    cy.get('input[name="password"]').type('secret')
    cy.get('form').submit()
    cy.getCookie('sessionid').should('exist')
  })
})
