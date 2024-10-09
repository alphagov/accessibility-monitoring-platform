/* global cy Cypress */

const loggedInUrls = [
  '/',
  '/accounts/password_reset/',
  '/accounts/password_reset/done/',
  '/audits/1/audit-retest-detail/',
  '/audits/1/edit-audit-metadata/',
  '/audits/1/edit-audit-report-options/',
  '/audits/1/edit-audit-retest-metadata/',
  '/audits/1/edit-audit-retest-statement-decision/',
  '/audits/1/edit-audit-statement-one/',
  '/audits/1/edit-audit-statement-two/',
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
  '/cases/1/edit-enforcement-recommendation/',
  '/cases/1/edit-case-close/',
  '/cases/1/edit-case-metadata/',
  '/cases/1/edit-no-psb-response/',
  '/cases/1/edit-post-case/',
  '/cases/1/edit-qa-auditor/',
  '/cases/1/edit-qa-comments/',
  '/cases/1/edit-qa-approval/',
  '/cases/1/edit-publish-report/',
  '/cases/1/edit-review-changes/',
  '/cases/1/edit-test-results/',
  '/cases/1/manage-contact-details/',
  '/cases/1/edit-contact-create/',
  '/cases/1/edit-request-contact-details/',
  '/cases/1/edit-one-week-contact-details/',
  '/cases/1/edit-four-week-contact-details/',
  '/cases/1/edit-report-sent-on/',
  '/cases/1/edit-report-one-week-followup/',
  '/cases/1/edit-report-four-week-followup/',
  '/cases/1/edit-report-acknowledged/',
  '/cases/1/edit-12-week-update-requested/',
  '/cases/1/edit-12-week-one-week-followup-final/',
  '/cases/1/edit-12-week-update-request-ack/',
  '/cases/1/edit-twelve-week-retest/',
  '/cases/1/outstanding-issues/',
  '/cases/1/email-template-list/',
  '/cases/1/1/email-template-preview/',
  '/cases/1/view/',
  '/cases/contacts/1/edit-contact-update/',
  '/cases/create/',
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
  '/common/report-issue/',
  '/common/email-template-list/',
  '/common/email-template-create/',
  '/common/1/email-template-preview/',
  '/common/1/email-template-update/',
  '/notifications/cases/1/reminder-task-create/',
  '/notifications/task-list/',
  '/reports/edit-report-wrapper/',
  '/reports/1/report-metrics-view/',
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
