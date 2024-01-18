/**
 * @jest-environment jsdom
 */

const sourceText = 'Text to copy'
const destinationId = 'notes'

document.body.innerHTML = `
 <span tabIndex="0"
    class="amp-control amp-copy-text"
    sourceText="${sourceText}"
    targetId="${destinationId}">
    Copy below
</span>
<textarea id="${destinationId}"></textarea>`

const {
  copyTextToInput,
  keyboardCopyTextToInput
} = require('../common/static/js/cases_copy_text')

describe('test cases copy text functions are present', () => {
  it.each([
    copyTextToInput,
    keyboardCopyTextToInput
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test copyTextToInput', () => {
  test('copy text happens (on click)', () => {
    document.getElementById(destinationId).value = ''
    copyTextToInput(destinationId, sourceText)
    expect(document.getElementById(destinationId).value).toEqual(sourceText)
  })
})

describe('test keyboardCopyTextToInput', () => {
  it.each([
    'Enter',
    'Space'
  ])('copy text happens when %p key pressed', (eventCode) => {
    document.getElementById(destinationId).value = ''
    const mockEvent = { preventDefault: jest.fn, code: eventCode }
    keyboardCopyTextToInput(mockEvent, destinationId, sourceText)
    expect(document.getElementById(destinationId).value).toEqual(sourceText)
  })

  test("copy text doesn't happen when neither enter nor space key pressed", () => {
    document.getElementById(destinationId).value = ''
    const mockEvent = { preventDefault: jest.fn, code: '' }
    keyboardCopyTextToInput(mockEvent, destinationId, sourceText)
    expect(document.getElementById(destinationId).value).toEqual('')
  })
})
