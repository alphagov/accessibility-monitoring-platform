
/* global cy, Cypress */

describe('Platform production Response headers', () => {
  it('include strict transport security', () => {
    cy.request('https://platform.accessibility-monitoring.service.gov.uk/').then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property('strict-transport-security', 'max-age=2592000; includeSubDomains; preload')
    })
  })
})
