/**
 * @jest-environment jsdom
 */

const url = 'https://example.com/'
const linkFieldId = 'link-field-id'
const openLinkControlId = `${linkFieldId}-open-link-control`

document.body.innerHTML = `
<div>
    <input type="text"
        name="accessibility_statement_backup_url"
        value="${url}"
        class="govuk-input"
        id="${linkFieldId}">
    <a class="govuk-link govuk-link--no-visited-state amp-open-link-control"
        id="${openLinkControlId}"
        data-input-field-id="${linkFieldId}"
        target="_blank"
        href="">
        Open link
    </a>
    <span class="govuk-body-s amp-margin-bottom-0 amp-margin-left-10">Open link</span>
 </div>`

const {
  updateOpenLinkControl
} = require('../common/static/js/url_field_dynamic_link')

describe('test common field link button functions are present', () => {
  it.each([
    updateOpenLinkControl
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test updateOpenLinkControl', () => {
  test('open link control displayed and populated with url', () => {
    updateOpenLinkControl(openLinkControlId, url)
    expect(document.getElementById(openLinkControlId).style.display).toEqual("block")
    expect(document.getElementById(openLinkControlId).href).toEqual(url)
  })
  test('open link placeholder not displayed', () => {
    updateOpenLinkControl(openLinkControlId, url)
    expect(document.getElementById(openLinkControlId).nextElementSibling.style.display).toEqual("none")
  })
  test('open link control not displayed with URL without https://', () => {
    updateOpenLinkControl(openLinkControlId, 'example.com')
    expect(document.getElementById(openLinkControlId).style.display).toEqual("none")
  })
  test('open link placeholder displayed', () => {
    updateOpenLinkControl(openLinkControlId, 'example.com')
    expect(document.getElementById(openLinkControlId).nextElementSibling.style.display).toEqual("block")
  })
})
