/* global cy, Cypress */

const hstsHeaderName = 'strict-transport-security'
const hstsHeaderValue = 'max-age=2592000; includeSubDomains; preload'

describe('Platform test response headers', () => {
  const domain = 'platform-test.accessibility-monitoring.service.gov.uk'
  it('include strict transport security', () => {
    cy.request(`https://${domain}/`).then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property(hstsHeaderName, hstsHeaderValue)
    })
  })
})

describe('Platform production response headers', () => {
  const domain = 'platform.accessibility-monitoring.service.gov.uk'
  it('include strict transport security', () => {
    cy.request(`https://${domain}/`).then((response) => {
      expect(response).to.have.property('headers')
      expect(response.headers).to.have.property(hstsHeaderName, hstsHeaderValue)
    })
  })
})
