
/* global cy, Cypress */

describe('Response headers', () => {
  it('include strict transport security', () => {
    cy.resuest('/').then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property('Strict-Transport-Security', 'max-age=2592000; includeSubDomains; preload')
  })
})
