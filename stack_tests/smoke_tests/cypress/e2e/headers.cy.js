
/* global cy, Cypress */

const hstsHeaderName = 'strict-transport-security'
const hstsHeaderValue = 'max-age=2592000; includeSubDomains; preload'

describe('Platform response headers', () => {
  it('include strict transport security', () => {
    cy.request('/').then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property(hstsHeaderName, hstsHeaderValue)
    })
  })
})
