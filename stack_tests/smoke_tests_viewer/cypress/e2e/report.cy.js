/* global cy */

describe('Accessibility monitoring report', () => {
  it('can see page', () => {
    cy.visit('/reports/7736f8ca-12eb-49f8-8599-a191e30b6a9a')
    cy.title().should('eq', 'Accessibility report for www.bedfordshire.pcc.police.uk')
  })
})
