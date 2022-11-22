/* global cy Cypress */

const loggedInUrls = [
  '/',
  '/accounts/password_reset/',
  '/accounts/password_reset/done/',
  '/audits/1/audit-retest-detail/',
  '/audits/1/detail/',
  '/audits/1/edit-audit-metadata/',
  '/audits/1/edit-audit-report-options/',
  '/audits/1/edit-audit-report-text/',
  '/audits/1/edit-audit-retest-metadata/',
  '/audits/1/edit-audit-retest-pages/',
  '/audits/1/edit-audit-retest-statement-decision/',
  '/audits/1/edit-audit-statement-one/',
  '/audits/1/edit-audit-statement-two/',
  '/audits/1/edit-audit-summary/',
  '/audits/1/edit-audit-pages/',
  '/audits/1/edit-retest-website-decision/',
  '/audits/1/edit-statement-decision/',
  '/audits/1/edit-website-decision/',
  '/audits/create-for-case/1/',
  '/audits/pages/1/edit-audit-page-checks/',
  '/audits/pages/1/edit-audit-retest-page-checks/',
  '/audits/wcag-definition-create/',
  '/audits/wcag-definition-list/',
  '/audits/1/edit-wcag-definition/',
  '/cases/',
  '/cases/1/edit-case-close/',
  '/cases/1/edit-case-details/',
  '/cases/1/edit-contact-details/',
  '/cases/1/edit-enforcement-body-correspondence/',
  '/cases/1/edit-final-statement/',
  '/cases/1/edit-final-website/',
  '/cases/1/edit-no-psb-response/',
  '/cases/1/edit-post-case/',
  '/cases/1/edit-qa-process/',
  '/cases/1/edit-report-correspondence/',
  '/cases/1/edit-report-details/',
  '/cases/1/edit-report-followup-due-dates/',
  '/cases/1/edit-review-changes/',
  '/cases/1/edit-test-results/',
  '/cases/1/edit-twelve-week-correspondence-due-dates/',
  '/cases/1/edit-twelve-week-correspondence/',
  '/cases/1/twelve-week-correspondence-email/',
  '/cases/1/edit-twelve-week-retest/',
  '/cases/1/view/',
  '/cases/create/',
  '/common/contact/',
  '/common/edit-active-qa-auditor/',
  '/common/markdown-cheatsheet/',
  '/common/metrics-case/',
  '/common/metrics-policy/',
  '/common/platform-versions/',
  '/common/report-issue/',
  '/notifications/notifications-list/',
  '/overdue/overdue-list/',
  '/reminders/cases/1/reminder-create/',
  '/reminders/reminder-list/',
  '/reports/edit-report-wrapper/',
  '/reports/1/report-publisher/',
  '/reports/1/edit-report/',
  '/reports/1/edit-report-metadata/',
  '/reports/1/report-metrics-view/',
  '/reports/sections/1/edit-section/',
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
    cy.login()
    Cypress.Cookies.preserveOnce('sessionid')
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
