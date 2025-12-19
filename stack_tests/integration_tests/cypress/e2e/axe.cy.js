/* global cy Cypress */

const loggedInUrls = [
  '/',
  '/accounts/password_reset/',
  '/accounts/password_reset/done/',
  '/audits/1/edit-audit-metadata/',
  '/audits/1/edit-audit-retest-metadata/',
  '/audits/1/edit-audit-retest-statement-decision/',
  '/audits/1/edit-audit-wcag-summary/',
  '/audits/1/edit-audit-pages/',
  '/audits/1/edit-retest-website-decision/',
  '/audits/1/edit-statement-decision/',
  '/audits/1/edit-website-decision/',
  '/audits/1/edit-statement-overview/',
  '/audits/1/edit-retest-statement-overview/',
  '/audits/1/edit-statement-website/',
  '/audits/1/edit-retest-statement-website/',
  '/audits/1/edit-statement-compliance/',
  '/audits/1/edit-retest-statement-compliance/',
  '/audits/1/edit-statement-non-accessible/',
  '/audits/1/edit-retest-statement-non-accessible/',
  '/audits/1/edit-statement-preparation/',
  '/audits/1/edit-retest-statement-preparation/',
  '/audits/1/edit-statement-feedback/',
  '/audits/1/edit-retest-statement-feedback/',
  '/audits/1/edit-statement-custom/',
  '/audits/1/edit-retest-statement-custom/',
  '/audits/create-for-case/1/',
  '/audits/pages/1/edit-audit-page-checks/',
  '/audits/pages/1/edit-audit-retest-page-checks/',
  '/audits/wcag-definition-create/',
  '/audits/wcag-definition-list/',
  '/audits/1/edit-wcag-definition/',
  '/cases/',
  '/simplified/1/edit-enforcement-recommendation/',
  '/simplified/1/edit-case-close/',
  '/simplified/1/edit-case-metadata/',
  '/simplified/1/edit-no-psb-response/',
  '/simplified/1/edit-qa-auditor/',
  '/simplified/1/edit-qa-comments/',
  '/simplified/1/edit-qa-approval/',
  '/simplified/1/edit-publish-report/',
  '/simplified/1/edit-review-changes/',
  '/simplified/1/edit-test-results/',
  '/simplified/1/manage-contact-details/',
  '/simplified/1/edit-contact-create/',
  '/simplified/1/edit-request-contact-details/',
  '/simplified/1/edit-one-week-contact-details/',
  '/simplified/1/edit-four-week-contact-details/',
  '/simplified/1/edit-report-sent-on/',
  '/simplified/1/edit-report-one-week-followup/',
  '/simplified/1/edit-report-four-week-followup/',
  '/simplified/1/edit-report-acknowledged/',
  '/simplified/1/edit-12-week-update-requested/',
  '/simplified/1/edit-12-week-one-week-followup-final/',
  '/simplified/1/edit-12-week-update-request-ack/',
  '/simplified/1/edit-twelve-week-retest/',
  '/simplified/1/outstanding-issues/',
  '/simplified/1/email-template-list/',
  '/simplified/1/1/email-template-preview/',
  '/simplified/1/view/',
  '/simplified/1/case-view-and-search/',
  '/simplified/contacts/1/edit-contact-update/',
  '/simplified/create/',
  '/common/contact/',
  '/common/edit-active-qa-auditor/',
  '/common/edit-frequently-used-links/',
  '/common/edit-footer-links/',
  '/common/markdown-cheatsheet/',
  '/common/more-information/',
  '/common/metrics-case/',
  '/common/metrics-policy/',
  '/common/metrics-report/',
  '/common/platform-versions/',
  '/notifications/cases/1/reminder-task-create/',
  '/notifications/task-list/',
  '/reports/edit-report-wrapper/',
  '/reports/1/report-metrics-view/',
  '/tech/',
  '/tech/platform-checking/',
  '/user/1/edit-user/'
]

const loggedOutUrls = [
  '/accounts/login/',
  '/user/register/'
]

const axeConfig = {
  includedImpacts: ['critical', 'serious']
}

describe('Axe core checks', () => {
  it('logged in urls', () => {
    cy.session('login', cy.login, { cacheAcrossSpecs: true })
    loggedInUrls.forEach(url => {
      cy.visit(url)
      cy.injectAxe()
      cy.checkA11y(null, axeConfig)
    })
  })

  it('logged out urls', () => {
    loggedOutUrls.forEach(url => {
      cy.visit(url)
      cy.injectAxe()
      cy.checkA11y(null, axeConfig)
    })
  })
})
