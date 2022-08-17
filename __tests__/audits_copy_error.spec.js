/**
 * @jest-environment jsdom
 */

const errorText = 'Error text to copy'
const sourceId = 'notes-0'
const destinationId = 'notes'

document.body.innerHTML = `<textarea id="${sourceId}" hidden>${errorText}</textarea>
 <span tabIndex="0"
    class="amp-copy-error"
    sourceId="${sourceId}"
    targetId="${destinationId}">
    Click to populate error details
</span>
<textarea id="${destinationId}" hidden></textarea>`

const {
  copyTextToInput,
  keyboardCopyTextToInput
} = require('../common/static/js/audits_copy_error')

describe('test audits copy error functions are present', () => {
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
    copyTextToInput(destinationId, sourceId)
    expect(document.getElementById(destinationId).value).toEqual(errorText)
  })
})

describe('test keyboardCopyTextToInput', () => {
  it.each([
    'Enter',
    'Space'
  ])('copy text happens when %p key pressed', (eventCode) => {
    document.getElementById(destinationId).value = ''
    const mockEvent = { preventDefault: jest.fn, code: eventCode }
    keyboardCopyTextToInput(mockEvent, destinationId, sourceId)
    expect(document.getElementById(destinationId).value).toEqual(errorText)
  })

  test("copy text doesn't happen when neither enter nor space key pressed", () => {
    document.getElementById(destinationId).value = ''
    const mockEvent = { preventDefault: jest.fn, code: '' }
    keyboardCopyTextToInput(mockEvent, destinationId, sourceId)
    expect(document.getElementById(destinationId).value).toEqual('')
  })
})
