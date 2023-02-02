/**
 * @jest-environment jsdom
 */

const summaryText = 'Summary text to copy'
const controlId = 'amp-copy-text-control'
const sourceId = 'copy-summary-source'
const destinationId = 'id_recommendation_notes'

document.body.innerHTML = `<textarea id="${sourceId}" hidden>${summaryText}</textarea>
 <a tabIndex="0"
    id="${controlId}">
    Click to populate summary text
</a>
<textarea id="${destinationId}"></textarea>`

const {
  copyTextToInput,
  keyboardCopyTextToInput
} = require('../common/static/js/cases_copy_summary')

describe('test cases copy summary functions are present', () => {
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
    const mockEvent = { preventDefault: jest.fn, code: '' }
    copyTextToInput(mockEvent)
    expect(document.getElementById(destinationId).value).toEqual(summaryText)
  })
})

describe('test keyboardCopyTextToInput', () => {
  it.each([
    'Enter',
    'Space'
  ])('copy text happens when %p key pressed', (eventCode) => {
    document.getElementById(destinationId).value = ''
    const mockEvent = { preventDefault: jest.fn, code: eventCode }
    keyboardCopyTextToInput(mockEvent)
    expect(document.getElementById(destinationId).value).toEqual(summaryText)
  })

  test("copy text doesn't happen when neither enter nor space key pressed", () => {
    document.getElementById(destinationId).value = ''
    const mockEvent = { preventDefault: jest.fn, code: '' }
    keyboardCopyTextToInput(mockEvent)
    expect(document.getElementById(destinationId).value).toEqual('')
  })
})
