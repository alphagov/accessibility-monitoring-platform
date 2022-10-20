/**
 * @jest-environment jsdom
 */

const textToCopy = 'Email text to copy'

document.body.innerHTML = `<div id="email-text">${textToCopy}</div>
<button class="copy-email-to-clipboard">
    Copy report to clipboard
</button>`

const {
  copyElementToClipboard
} = require('../common/static/js/cases_copy_email')

describe('test cases copy email function is present', () => {
  it.each([
    copyElementToClipboard
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test copyElementToClipboard', () => {
  test('copy text to clipboard happens (on click)', () => {
    document.execCommand = jest.fn()
    copyElementToClipboard()
    expect(document.execCommand).toHaveBeenCalledWith('copy')
  })
})
