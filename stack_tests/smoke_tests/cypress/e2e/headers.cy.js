
/* global cy, Cypress */

describe('Platform staging response headers', () => {
  it('include strict transport security', () => {
    cy.request('/').then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property('strict-transport-security', 'max-age=2592000; includeSubDomains; preload')
    })
  })
})
describe('Platform test response headers', () => {
  it('include strict transport security', () => {
    cy.request('https://platform-test.accessibility-monitoring.service.gov.uk/').then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property('strict-transport-security', 'max-age=2592000; includeSubDomains; preload')
    })
  })
})
describe('Platform production response headers', () => {
  it('include strict transport security', () => {
    cy.request('https://platform.accessibility-monitoring.service.gov.uk/').then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property('strict-transport-security', 'max-age=2592000; includeSubDomains; preload')
    })
  })
})
