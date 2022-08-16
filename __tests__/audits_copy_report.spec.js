/**
 * @jest-environment jsdom
 */
const textToCopy = 'Report text to copy'

document.body.innerHTML = `<div id="report-text">${textToCopy}</div>
<button id="copy-report-to-clipboard">
    Copy report to clipboard
</button>`

const {
  copyElementToClipboard
} = require('../common/static/js/audits_copy_report')

describe('test audits copy report functions are present', () => {
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
